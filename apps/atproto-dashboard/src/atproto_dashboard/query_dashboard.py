"""Query the dashboard data from DuckDB"""

from pathlib import Path

import duckdb


def query_dashboard_data():
    """Query the dbt models and display dashboard data"""
    db_path = Path(__file__).parent.parent.parent / "dbt_project" / "local.duckdb"

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        print("Run the pipeline first: python -m atproto_dashboard.pipeline")
        return

    conn = duckdb.connect(str(db_path))

    print("=" * 60)
    print("ATProto Dashboard - Powered by Prefect Assets")
    print("=" * 60)

    # List all tables/views
    print("\nAvailable tables/views:")
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'atproto'"
    ).fetchall()
    for table in tables:
        print(f"  - {table[0]}")

    # Show daily activity
    print("\n📊 Daily Activity:")
    try:
        daily_activity = conn.execute("""
            SELECT 
                day,
                total_posts,
                total_likes,
                total_replies,
                total_quotes
            FROM atproto.daily_activity
            ORDER BY day DESC
            LIMIT 7
        """).fetchall()

        print(
            f"{'Date':<12} {'Posts':<10} {'Likes':<10} {'Replies':<10} {'Quotes':<10}"
        )
        print("-" * 52)
        for row in daily_activity:
            print(f"{row[0]:<12} {row[1]:<10} {row[2]:<10} {row[3]:<10} {row[4]:<10}")
    except Exception as e:
        print(f"  (Query failed: {e})")

    # Show top posts
    print("\n🔥 Top Posts (by engagement):")
    try:
        top_posts = conn.execute("""
            SELECT 
                author_handle,
                SUBSTRING(text, 1, 50) || '...' as text_preview,
                likes,
                replies,
                quotes
            FROM atproto.top_posts
            ORDER BY likes DESC
            LIMIT 5
        """).fetchall()

        print(f"{'Author':<20} {'Post':<35} {'Likes':<8} {'Replies':<8} {'Quotes':<8}")
        print("-" * 79)
        for row in top_posts:
            print(f"{row[0]:<20} {row[1]:<35} {row[2]:<8} {row[3]:<8} {row[4]:<8}")
    except Exception as e:
        print(f"  (Query failed: {e})")

    # Show user stats
    print("\n👥 User Statistics:")
    try:
        user_stats = conn.execute("""
            SELECT 
                author_handle,
                COUNT(*) as post_count,
                SUM(likes) as total_likes,
                ROUND(AVG(likes), 2) as avg_likes
            FROM atproto.stg_feeds
            GROUP BY author_handle
            ORDER BY total_likes DESC
        """).fetchall()

        print(f"{'Handle':<25} {'Posts':<10} {'Total Likes':<12} {'Avg Likes':<10}")
        print("-" * 57)
        for row in user_stats:
            print(f"{row[0]:<25} {row[1]:<10} {row[2]:<12} {row[3]:<10}")
    except Exception as e:
        print(f"  (Query failed: {e})")

    print("\n" + "=" * 60)
    print("💡 Tip: Run 'python -m atproto_dashboard.pipeline' to refresh data")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    query_dashboard_data()
