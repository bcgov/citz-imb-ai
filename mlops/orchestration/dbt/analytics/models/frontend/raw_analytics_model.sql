{{ config(materialized='table') }}

SELECT
    data->>'sessionTimestamp' AS session_timestamp,
    data->>'sessionId' AS session_id,
    data->>'userId' AS user_id,
    data->'chats' AS chats
FROM {{ source('frontend_analytics', 'raw_frontend_analytics') }}
