WITH raw AS (
    SELECT * FROM {{ source('s3_raw', 'actor_feed_snapshot') }}
)

SELECT 
    json_extract_string(json, '$.post.author.handle') AS author_handle,
    json_extract_string(json, '$.post.author.did') AS author_did,
    CAST(json.post.like_count AS INT) AS likes,
    CAST(json.post.quote_count AS INT) AS quotes,
    CAST(json.post.reply_count AS INT) AS replies,
    json_extract_string(json, '$.post.record.text') AS post_text,
    CAST(json.post.record.created_at AS TIMESTAMP) AS created_at,
    filename,
    strptime(
        regexp_extract(
            filename,
            's3://[^/]+/atproto_actor_feed_snapshot/(\d{4}-\d{2}-\d{2}/\d{2}/\d{2})',
            1
        ),
        '%Y-%m-%d/%H/%M'
    ) AS snapshot_timestamp
FROM raw