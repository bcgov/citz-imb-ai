{{ config(materialized='table') }}

SELECT
    {{ dbt_utils.generate_surrogate_key(["data->>'sessionId'", "chat->>'llmResponseId'", "chat->'llmResponseInteraction'->>'chatIndex'"]) }} AS interaction_id,
    {{ dbt_utils.generate_surrogate_key(["data->>'sessionId'", "chat->>'llmResponseId'"]) }} AS chat_id,
    (chat->'llmResponseInteraction'->>'chatIndex')::int AS chat_index,
    (chat->'llmResponseInteraction'->>'clicks')::int AS clicks,
    (chat->'llmResponseInteraction'->>'hoverDuration')::float AS hover_duration,
    (chat->'llmResponseInteraction'->>'lastClickTimestamp')::timestamp AS last_click_timestamp
FROM {{ source('frontend_analytics', 'raw_frontend_analytics') }},
    jsonb_array_elements(data->'chats') AS chat
