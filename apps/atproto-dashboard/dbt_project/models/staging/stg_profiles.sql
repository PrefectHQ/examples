WITH raw AS (
    SELECT * FROM {{ source('s3_raw', 'starter_pack_snapshot') }}
)

SELECT 
    json_extract_string(json, '$.subject.handle') AS handle,
    json_extract_string(json, '$.subject.did') AS did,
    json_extract_string(json, '$.subject.display_name') AS display_name,
    json_extract_string(json, '$.subject.description') AS description,
    json_extract_string(json, '$.subject.avatar') AS avatar_url,
    CAST(json_extract_string(json, '$.subject.created_at') AS TIMESTAMP) AS created_at,
    filename,
    strptime(
        regexp_extract(
            filename,
            's3://[^/]+/atproto_starter_pack_snapshot/(\d{4}-\d{2}-\d{2}/\d{2}/\d{2})',
            1
        ),
        '%Y-%m-%d/%H/%M'
    ) AS snapshot_timestamp
FROM raw