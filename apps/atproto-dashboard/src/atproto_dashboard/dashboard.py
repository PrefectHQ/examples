"""Streamlit dashboard for ATProto data visualization"""

import json

import pandas as pd
import streamlit as st
from prefect_aws import S3Bucket

from atproto_dashboard.settings import settings

st.set_page_config(
    page_title="ATProto Dashboard - Prefect Assets", page_icon="🦋", layout="wide"
)

st.title("🦋 ATProto Dashboard")
st.caption("Powered by Prefect Assets")


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data_from_s3():
    """Load the latest data from S3 assets"""
    s3_bucket = S3Bucket(bucket_name=settings.aws_bucket_name)

    # Load starter pack members
    members_data = s3_bucket.read_path("assets/starter-pack-members/latest.json")
    members = json.loads(members_data)

    # Load actor feeds
    feeds_data = s3_bucket.read_path("assets/actor-feeds/latest.json")
    feeds = json.loads(feeds_data)

    # Convert feeds to DataFrame for analysis
    all_posts = []
    for actor_did, actor_posts in feeds.items():
        for post in actor_posts:
            post["actor_did"] = actor_did
            all_posts.append(post)

    df_posts = pd.DataFrame(all_posts)
    df_members = pd.DataFrame(members)

    return df_members, df_posts


try:
    df_members, df_posts = load_data_from_s3()

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Overview", "👥 Members", "📝 Posts", "🔍 Analysis"]
    )

    with tab1:
        st.header("Dashboard Overview")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Members", len(df_members))
        with col2:
            st.metric("Total Posts", len(df_posts))
        with col3:
            avg_likes = df_posts["likes"].mean()
            st.metric("Avg Likes/Post", f"{avg_likes:.1f}")
        with col4:
            avg_replies = df_posts["replies"].mean()
            st.metric("Avg Replies/Post", f"{avg_replies:.1f}")

        # Engagement by user
        st.subheader("📈 Engagement by User")
        user_stats = (
            df_posts.groupby("author_handle")
            .agg(
                {
                    "likes": ["sum", "mean"],
                    "replies": ["sum", "mean"],
                    "quotes": ["sum", "mean"],
                    "author_handle": "count",
                }
            )
            .round(2)
        )
        user_stats.columns = [
            "Total Likes",
            "Avg Likes",
            "Total Replies",
            "Avg Replies",
            "Total Quotes",
            "Avg Quotes",
            "Post Count",
        ]
        user_stats = user_stats.sort_values("Total Likes", ascending=False)

        st.dataframe(user_stats, use_container_width=True)

    with tab2:
        st.header("Starter Pack Members")
        st.dataframe(df_members, use_container_width=True)

    with tab3:
        st.header("Recent Posts")

        # Filter by author
        selected_author = st.selectbox(
            "Filter by author",
            ["All"] + sorted(df_posts["author_handle"].unique().tolist()),
        )

        if selected_author != "All":
            filtered_posts = df_posts[df_posts["author_handle"] == selected_author]
        else:
            filtered_posts = df_posts

        # Sort by engagement
        sort_by = st.selectbox("Sort by", ["likes", "replies", "quotes", "created_at"])
        filtered_posts = filtered_posts.sort_values(sort_by, ascending=False)

        # Display posts
        for _, post in filtered_posts.head(20).iterrows():
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**@{post['author_handle']}** - {post['created_at']}")
                    st.write(
                        post["text"][:280] + "..."
                        if len(post["text"]) > 280
                        else post["text"]
                    )
                with col2:
                    st.caption(
                        f"❤️ {post['likes']} | 💬 {post['replies']} | 🔄 {post['quotes']}"
                    )
                st.divider()

    with tab4:
        st.header("Analysis")

        # Top posts by likes
        st.subheader("🔥 Top 10 Posts by Likes")
        top_posts = df_posts.nlargest(10, "likes")[
            ["author_handle", "text", "likes", "replies", "quotes"]
        ]
        st.dataframe(top_posts, use_container_width=True)

        # Engagement distribution
        st.subheader("📊 Engagement Distribution")

        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(
                df_posts.groupby("author_handle")["likes"]
                .sum()
                .sort_values(ascending=True)
            )
            st.caption("Total Likes by Author")

        with col2:
            st.bar_chart(
                df_posts.groupby("author_handle").size().sort_values(ascending=True)
            )
            st.caption("Post Count by Author")

    # Sidebar with refresh info
    st.sidebar.header("ℹ️ Dashboard Info")
    st.sidebar.info(
        "This dashboard reads directly from Prefect Assets stored in S3. "
        "Data is cached for 5 minutes."
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "To refresh data, run:\n```bash\npython -m atproto_dashboard.pipeline\n```"
    )

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info(
        "Make sure you've run the pipeline at least once: `python -m atproto_dashboard.pipeline`"
    )
