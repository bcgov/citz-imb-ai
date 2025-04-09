-- models/unified/trulens_frontend_unified.sql

WITH trulens_data AS (
    SELECT
        tr.record_id,
        tr.input,
        tr.output,
        tr.ts,
        tf.result,
        tf.calls_json,
        CASE 
            WHEN tf.calls_json::jsonb->'calls' IS NOT NULL THEN
                jsonb_agg(call_element->'meta'->>'reason') FILTER (WHERE call_element->'meta'->>'reason' IS NOT NULL)
            ELSE NULL
        END AS reason_comments
    FROM 
        {{ source('trulens', 'trulens_records') }} tr
    LEFT JOIN 
        {{ source('trulens', 'trulens_feedbacks') }} tf
    ON 
        tr.record_id = tf.record_id
    LEFT JOIN LATERAL 
        jsonb_array_elements(tf.calls_json::jsonb->'calls') AS call_element
    ON 
        true
    GROUP BY
        tr.record_id, tr.input, tr.output, tr.ts, tf.result, tf.calls_json
),

frontend_data AS (
    SELECT
        record_id,
        total_clicks,
        source_clicks,
        
        -- Extract top 10 clicks - expand the JSON into columns
        COALESCE((source_clicks->>'0')::int, 0) AS response_0_clicks,
        COALESCE((source_clicks->>'1')::int, 0) AS response_1_clicks,
        COALESCE((source_clicks->>'2')::int, 0) AS response_2_clicks,
        COALESCE((source_clicks->>'3')::int, 0) AS response_3_clicks,
        COALESCE((source_clicks->>'4')::int, 0) AS response_4_clicks,
        COALESCE((source_clicks->>'5')::int, 0) AS response_5_clicks,
        COALESCE((source_clicks->>'6')::int, 0) AS response_6_clicks,
        COALESCE((source_clicks->>'7')::int, 0) AS response_7_clicks,
        COALESCE((source_clicks->>'8')::int, 0) AS response_8_clicks,
        COALESCE((source_clicks->>'9')::int, 0) AS response_9_clicks
    FROM
        {{ source('frontend', 'record_id_clicks') }}
)

SELECT
    -- Primary key and join fields
    COALESCE(t.record_id, f.record_id) AS record_id,
    
    -- Trulens data
    t.input,
    t.output,
    t.ts AS timestamp,
    t.result,
    t.reason_comments,
    
    -- Frontend analytics data
    f.total_clicks,
    f.source_clicks AS source_clicks_json,
    
    -- Expanded source clicks
    f.response_0_clicks,
    f.response_1_clicks,
    f.response_2_clicks,
    f.response_3_clicks,
    f.response_4_clicks,
    f.response_5_clicks,
    f.response_6_clicks,
    f.response_7_clicks,
    f.response_8_clicks,
    f.response_9_clicks,
    
    -- Calculate engagement metrics
    CASE 
        WHEN f.total_clicks IS NULL THEN false
        WHEN f.total_clicks > 0 THEN true
        ELSE false
    END AS has_engagement,
    
    -- Data presence flags
    CASE WHEN t.record_id IS NOT NULL THEN true ELSE false END AS has_trulens_data,
    CASE WHEN f.record_id IS NOT NULL THEN true ELSE false END AS has_frontend_data
FROM
    trulens_data t
FULL OUTER JOIN
    frontend_data f
ON
    t.record_id = f.record_id