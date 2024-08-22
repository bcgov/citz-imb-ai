{{ config(materialized='table') }}

SELECT DISTINCT
    data->>'sessionId' AS session_id,
    (data->>'sessionTimestamp')::timestamp AS session_timestamp,
    data->>'userId' AS user_id
FROM {{ source('frontend_analytics', 'raw_data') }}
