{{ config(materialized='table') }}

SELECT
    {{ dbt_utils.generate_surrogate_key(["data->>'sessionId'", "chat->>'llmResponseId'"]) }} AS chat_id,
    data->>'sessionId' AS session_id,
    chat->>'llmResponseId' AS llm_response_id,
    chat->>'recording_id' AS recording_id,
    (chat->>'timestamp')::timestamp AS timestamp,
    (chat->'llmResponseInteraction'->>'chatIndex')::int AS chat_index,
    (chat->'llmResponseInteraction'->>'clicks')::int AS llm_response_clicks,
    (chat->'llmResponseInteraction'->>'hoverDuration')::float AS llm_response_hover_duration,
    NULLIF(chat->'llmResponseInteraction'->>'lastClickTimestamp', '')::timestamp AS llm_response_last_click_timestamp
FROM {{ source('frontend', 'raw_frontend_analytics') }},
    jsonb_array_elements(data->'chats') AS chat
