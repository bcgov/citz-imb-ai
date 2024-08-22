{{ config(materialized='table') }}

SELECT
    {{ dbt_utils.generate_surrogate_key(["data->>'sessionId'", "chat->>'llmResponseId'"]) }} AS chat_id,
    data->>'sessionId' AS session_id,
    chat->>'llmResponseId' AS llm_response_id,
    chat->>'recording_id' AS recording_id,
    (chat->>'timestamp')::timestamp AS timestamp
FROM {{ source('frontend_analytics', 'raw_frontend_analytics') }},
    jsonb_array_elements(data->'chats') AS chat
