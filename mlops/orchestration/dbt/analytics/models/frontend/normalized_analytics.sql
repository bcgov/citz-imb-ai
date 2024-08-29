{{ config(materialized='table') }}

WITH chat_data AS (
    SELECT
        data->>'sessionId' AS session_id,
        (data->>'sessionTimestamp')::timestamp AS session_timestamp,
        data->>'userId' AS user_id,
        chat->>'llmResponseId' AS llm_response_id,
        chat->>'recording_id' AS record_id,
        (chat->>'timestamp')::timestamp AS chat_timestamp,
        (chat->'llmResponseInteraction'->>'chatIndex')::int AS chat_index,
        (chat->'llmResponseInteraction'->>'clicks')::int AS llm_response_clicks,
        (chat->'llmResponseInteraction'->>'hoverDuration')::float AS llm_response_hover_duration,
        NULLIF(chat->'llmResponseInteraction'->>'lastClickTimestamp', '')::timestamp AS llm_response_last_click_timestamp,
        chat->'sources' AS sources
    FROM 
        {{ source('frontend', 'raw_frontend_analytics') }},
        jsonb_array_elements(data->'chats') AS chat
)

SELECT
    record_id,
    session_id,
    session_timestamp,
    user_id,
    llm_response_id,
    chat_index,
    chat_timestamp,
    llm_response_clicks,
    llm_response_hover_duration,
    llm_response_last_click_timestamp,
    {{ unroll_frontend_json_to_columns('sources', 10) }}
FROM chat_data
