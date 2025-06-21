import json
from datetime import datetime

from prefect import flow
from prefect.artifacts import create_markdown_artifact
from prefect.assets import materialize
from prefect_aws import S3Bucket

from atproto_dashboard.resources.atproto_client import get_atproto_client
from atproto_dashboard.settings import settings


def get_s3_bucket() -> S3Bucket:
    """Get configured S3 bucket block."""
    # S3Bucket will automatically use ~/.aws/credentials if no keys are provided
    return S3Bucket(
        bucket_name=settings.aws_bucket_name,
    )


def fetch_author_feed_page(client, actor: str, cursor: str | None = None) -> dict:
    """Fetch a page of author feed."""
    return client.get_author_feed(actor=actor, cursor=cursor, limit=100)


@materialize(f"s3://{settings.aws_bucket_name}/assets/starter-pack-members/latest.json")
def materialize_starter_pack_members(starter_pack_uri: str) -> list[dict]:
    """
    Materialize starter pack members as a Prefect Asset.
    """
    client = get_atproto_client().get_client()

    # Get the starter pack
    response = client.app.bsky.graph.get_starter_pack(
        {"starter_pack": starter_pack_uri}
    )
    list_uri = response.starter_pack.list.uri

    # Get all members from the list
    members = []
    cursor = None

    while True:
        list_response = client.app.bsky.graph.get_list(
            {"list": list_uri, "cursor": cursor, "limit": 100}
        )
        members.extend(list_response.items)
        if not list_response.cursor:
            break
        cursor = list_response.cursor

    # Store raw data to S3
    timestamp = datetime.now()
    key = f"atproto_starter_pack_snapshot/{timestamp:%Y-%m-%d/%H/%M}/{starter_pack_uri}.json"

    content = "\n".join(member.model_dump_json() for member in members)
    s3_bucket = get_s3_bucket()
    s3_bucket.write_path(key, content.encode("utf-8"))

    # Also store as the "latest" asset
    structured_data = [
        {
            "did": member.subject.did,
            "handle": member.subject.handle,
            "display_name": member.subject.display_name,
        }
        for member in members
    ]

    s3_bucket.write_path(
        "assets/starter-pack-members/latest.json",
        json.dumps(structured_data).encode("utf-8"),
    )

    # Create artifact for visibility
    create_markdown_artifact(
        key="starter-pack-snapshot",
        markdown=f"""
# Starter Pack Snapshot

- **URI**: {starter_pack_uri}
- **Members**: {len(members)}
- **S3 Location**: s3://{s3_bucket.bucket_name}/{key}
- **Asset Location**: s3://{s3_bucket.bucket_name}/assets/starter-pack-members/latest.json
- **Timestamp**: {timestamp}
""",
        description="Starter pack member snapshot",
    )

    return structured_data


@materialize(
    f"s3://{settings.aws_bucket_name}/assets/actor-feeds/latest.json",
    asset_deps=[
        f"s3://{settings.aws_bucket_name}/assets/starter-pack-members/latest.json"
    ],
)
def materialize_actor_feeds() -> dict[str, list[dict]]:
    """
    Materialize actor feeds as a Prefect Asset.
    Depends on the starter pack members asset.
    """
    # Read the starter pack members from the asset
    s3_bucket = get_s3_bucket()

    members_data = s3_bucket.read_path("assets/starter-pack-members/latest.json")
    members = json.loads(members_data)

    all_feeds = {}
    client = get_atproto_client().get_client()

    for member in members:
        did = member["did"]

        print(f"Fetching feed for {member['handle']}...")

        # Just get the first page of recent posts (up to 100)
        response = fetch_author_feed_page(client, did, cursor=None)
        feeds = response.feed

        # Store individual raw feed
        timestamp = datetime.now()
        key = f"atproto_actor_feed_snapshot/{timestamp:%Y-%m-%d/%H/%M}/{did}.json"

        content = "\n".join(feed.model_dump_json() for feed in feeds)
        s3_bucket.write_path(key, content.encode("utf-8"))

        # Extract key fields for the asset
        all_feeds[did] = [
            {
                "author_handle": feed.post.author.handle,
                "author_did": feed.post.author.did,
                "text": feed.post.record.text
                if hasattr(feed.post.record, "text")
                else "",
                "created_at": str(feed.post.record.created_at)
                if hasattr(feed.post.record, "created_at")
                else "",
                "likes": feed.post.like_count
                if hasattr(feed.post, "like_count")
                else 0,
                "replies": feed.post.reply_count
                if hasattr(feed.post, "reply_count")
                else 0,
                "quotes": feed.post.quote_count
                if hasattr(feed.post, "quote_count")
                else 0,
            }
            for feed in feeds
        ]

        print(f"Stored {len(feeds)} feed items for {member['handle']}")

    # Store the asset
    s3_bucket.write_path(
        "assets/actor-feeds/latest.json", json.dumps(all_feeds).encode("utf-8")
    )

    return all_feeds


@flow(name="ingest-atproto-data")
def ingest_atproto_data(starter_pack_uri: str) -> dict:
    """
    Main flow to ingest ATProto data as Prefect Assets.
    """
    # Materialize starter pack members
    members = materialize_starter_pack_members(starter_pack_uri)
    print(f"Materialized {len(members)} members as asset")

    # Materialize actor feeds (depends on members)
    feeds = materialize_actor_feeds()

    total_posts = sum(len(actor_feeds) for actor_feeds in feeds.values())

    summary = {
        "starter_pack_uri": starter_pack_uri,
        "members_count": len(members),
        "total_posts": total_posts,
        "timestamp": datetime.now().isoformat(),
    }

    create_markdown_artifact(
        key="ingestion-summary",
        markdown=f"""
# ATProto Ingestion Summary

- **Starter Pack**: {starter_pack_uri}
- **Members Processed**: {len(members)}
- **Total Posts**: {total_posts}
- **Timestamp**: {summary["timestamp"]}

## Assets Created
- `s3://{settings.aws_bucket_name}/assets/starter-pack-members/latest.json`
- `s3://{settings.aws_bucket_name}/assets/actor-feeds/latest.json`
""",
        description="Summary of ATProto data ingestion",
    )

    return summary


if __name__ == "__main__":
    # Run the flow
    ingest_atproto_data()
