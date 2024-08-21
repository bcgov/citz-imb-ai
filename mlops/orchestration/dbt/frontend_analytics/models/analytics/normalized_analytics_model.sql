{{ config(materialized='table') }}

WITH chat_data AS (
  SELECT
    session_timestamp,
    session_id,
    user_id,
    jsonb_array_elements(chats) AS chat
  FROM {{ ref('raw_frontend_analytics') }}
),
source_data AS (
  SELECT
    session_timestamp,
    session_id,
    user_id,
    chat->>'llmResponseId' AS llm_response_id,
    chat->>'recording_id' AS recording_id,
    chat->>'timestamp' AS chat_timestamp,
    (chat->'llmResponseInteraction'->>'chatIndex')::int AS chat_index,
    (chat->'llmResponseInteraction'->>'clicks')::int AS llm_response_clicks,
    (chat->'llmResponseInteraction'->>'hoverDuration')::float AS llm_response_hover_duration,
    chat->'llmResponseInteraction'->>'lastClickTimestamp' AS llm_response_last_click_timestamp,
    jsonb_array_elements(chat->'sources') AS source
  FROM chat_data
)
SELECT
  session_timestamp,
  session_id,
  user_id,
  llm_response_id,
  recording_id,
  chat_timestamp,
  chat_index,
  llm_response_clicks,
  llm_response_hover_duration,
  llm_response_last_click_timestamp,
  (source->>'chatIndex')::int AS source_chat_index,
  (source->>'sourceKey')::int AS source_key,
  source->>'response' AS source_response,
  (source->>'clicks')::int AS source_clicks,
  source->>'lastClickTimestamp' AS source_last_click_timestamp
FROM source_data
