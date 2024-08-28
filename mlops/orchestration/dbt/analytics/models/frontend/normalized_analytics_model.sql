{{ config(materialized='table') }}

WITH chat_data AS (
  SELECT
    data->>'sessionTimestamp' AS session_timestamp,
    data->>'sessionId' AS session_id,
    data->>'userId' AS user_id,
    jsonb_array_elements(data->'chats') AS chat
  FROM {{ source('frontend', 'raw_frontend_analytics') }}
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
),
trulens_data AS (
  SELECT *
  FROM {{ ref('trulens_normalize') }}
)
SELECT
  sd.session_timestamp,
  sd.session_id,
  sd.user_id,
  sd.llm_response_id,
  sd.recording_id,
  sd.chat_timestamp,
  sd.chat_index,
  sd.llm_response_clicks,
  sd.llm_response_hover_duration,
  sd.llm_response_last_click_timestamp,
  (sd.source->>'chatIndex')::int AS source_chat_index,
  (sd.source->>'sourceKey')::int AS source_key,
  sd.source->>'response' AS source_response,
  (sd.source->>'clicks')::int AS source_clicks,
  sd.source->>'lastClickTimestamp' AS source_last_click_timestamp,
  td.input AS trulens_input,
  td.output AS trulens_output,
  td.latency_in_seconds AS trulens_latency,
  td.start_time AS trulens_start_time,
  td.end_time AS trulens_end_time
FROM source_data sd
LEFT JOIN trulens_data td ON sd.recording_id = td.record_id
