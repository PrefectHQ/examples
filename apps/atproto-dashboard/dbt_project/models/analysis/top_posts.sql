WITH latest_feeds AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY author_handle, post_text
            ORDER BY snapshot_timestamp DESC
        ) AS rn
    FROM {{ ref('stg_feeds') }}
),

scored_posts AS (
    SELECT 
        author_handle,
        post_text,
        likes,
        quotes,
        replies,
        created_at,
        -- Engagement score: weighted sum of interactions
        (likes * 0.2) + (quotes * 0.4) + (replies * 0.4) AS engagement_score
    FROM latest_feeds
    WHERE rn = 1
)

SELECT 
    author_handle,
    post_text,
    likes,
    quotes,
    replies,
    ROUND(engagement_score, 2) AS engagement_score,
    created_at,
    ROW_NUMBER() OVER (ORDER BY engagement_score DESC) AS rank
FROM scored_posts
WHERE LENGTH(post_text) > 10  -- Filter out very short posts
ORDER BY engagement_score DESC
LIMIT 100