WITH raw_data AS (
    SELECT 
        record_id,
        app_id,  
        input,
        output,
        ts,
        record_json::json AS record_json
    FROM 
        {{ source('simple', 'records') }}  -- Use dbt's source function
), 
parsed_data AS (
    SELECT 
        record_id,
        input,
        ts,
        record_json->'calls'->2->'rets' AS LLM_output,
        {{ unroll_json_to_columns('record_json', 10) }},  -- Replace static SQL with dynamic macro call
        record_json->>'record_id' AS json_record_id,  
        record_json->'app_id' AS app_id,
        (record_json->'perf'->>'start_time')::timestamp AS start_time,
        (record_json->'perf'->>'end_time')::timestamp AS end_time,
        -- Calculate latency in seconds
        EXTRACT(EPOCH FROM ((record_json->'perf'->>'end_time')::timestamp - (record_json->'perf'->>'start_time')::timestamp)) AS latency_in_seconds, 
        {{ extract_performance('record_json', 4) }}  -- Replace static SQL with dynamic macro call
    FROM 
        raw_data
),
feedback_data AS (
    SELECT 
        record_id,
        array_agg(result) AS result  -- Replace this with actual column names in feedbacks
    FROM 
        {{ source('simple', 'feedbacks') }}  -- Join feedbacks table
    GROUP BY 
        record_id  -- Group by record_id to aggregate feedbacks
)

-- Final SELECT statement to retrieve data from the last CTE
-- SELECT *
-- FROM parsed_data

-- Final join to merge parsed_data with feedback_data based on record_id hash
SELECT 
    pd.*,
    fb.result  -- Include feedback details
FROM 
    parsed_data pd
LEFT JOIN 
    feedback_data fb
    ON pd.record_id = fb.record_id