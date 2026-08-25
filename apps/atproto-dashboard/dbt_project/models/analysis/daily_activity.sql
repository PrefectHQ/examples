WITH latest_feeds AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY author_handle, post_text, DATE_TRUNC('day', created_at)
            ORDER BY snapshot_timestamp DESC
        ) AS rn
    FROM {{ ref('stg_feeds') }}
)

SELECT 
    DATE_TRUNC('day', created_at) AS activity_date,
    COUNT(DISTINCT author_handle) AS unique_authors,
    COUNT(*) AS total_posts,
    SUM(likes) AS total_likes,
    SUM(quotes) AS total_quotes,
    SUM(replies) AS total_replies,
    AVG(likes) AS avg_likes_per_post,
    AVG(quotes) AS avg_quotes_per_post,
    AVG(replies) AS avg_replies_per_post
FROM latest_feeds
WHERE rn = 1
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY activity_date DESC