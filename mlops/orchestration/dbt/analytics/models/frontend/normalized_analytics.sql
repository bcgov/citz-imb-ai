{{ config(materialized='table') }}

SELECT
    data->>'sessionId' AS session_id,
    (data->>'sessionTimestamp')::timestamp AS session_timestamp,
    data->>'userId' AS user_id,
    c.chat_id,
    c.llm_response_id,
    c.recording_id,
    c.timestamp AS chat_timestamp,
    c.chat_index,
    c.llm_response_clicks,
    c.llm_response_hover_duration,
    c.llm_response_last_click_timestamp,
    src.source_id,
    src.source_key,
    src.response AS source_response,
    src.clicks AS source_clicks,
    src.last_click_timestamp AS source_last_click_timestamp,
    td.input AS trulens_input,
    td.LLM_output AS trulens_output,
    td.latency_in_seconds AS trulens_latency,
    td.start_time AS trulens_start_time,
    td.end_time AS trulens_end_time
FROM {{ source('frontend', 'raw_frontend_analytics') }}
JOIN {{ ref('chats') }} c ON data->>'sessionId' = c.session_id
LEFT JOIN {{ ref('sources') }} src ON c.chat_id = src.chat_id
LEFT JOIN {{ ref('trulens_normalize') }} td ON c.recording_id = td.record_id
