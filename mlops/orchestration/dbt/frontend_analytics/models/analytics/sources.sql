{{ config(materialized='table') }}

SELECT
    {{ dbt_utils.generate_surrogate_key(["data->>'sessionId'", "chat->>'llmResponseId'", "source->>'sourceKey'"]) }} AS source_id,
    {{ dbt_utils.generate_surrogate_key(["data->>'sessionId'", "chat->>'llmResponseId'"]) }} AS chat_id,
    (source->>'chatIndex')::int AS chat_index,
    (source->>'sourceKey')::int AS source_key,
    source->>'response' AS response,
    (source->>'clicks')::int AS clicks,
    (source->>'lastClickTimestamp')::timestamp AS last_click_timestamp
FROM {{ source('frontend_analytics', 'raw_frontend_analytics') }},
    jsonb_array_elements(data->'chats') AS chat,
    jsonb_array_elements(chat->'sources') AS source
