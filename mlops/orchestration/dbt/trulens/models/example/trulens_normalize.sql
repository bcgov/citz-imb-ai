WITH raw_data AS (
    SELECT 
        record_id,
        app_id,  
        input,
        output,
        record_json::json AS record_json
    FROM 
        {{ source('public', 'records') }}  -- Use dbt's source function
    WHERE
        app_id = 'TopK_Feedback_System_v1'    
), 
parsed_data AS (
    SELECT 
        record_id,
        input,
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
)

-- Final SELECT statement to retrieve data from the last CTE
SELECT *
FROM parsed_data
