WITH raw_data AS (
    SELECT 
        record_id,
        app_id,  
        input,
        output,
        ts,
        record_json::json AS record_json
    FROM 
        {{ source('public', 'records') }}  -- Use dbt's source function
    -- Removing app_id filter to show all data
)

SELECT 
    record_id,
    input,
    ts,
    record_json->'calls'->2->'rets' AS LLM_output,
    record_json->>'record_id' AS json_record_id,  
    record_json->'app_id' AS app_id,
    (record_json->'perf'->>'start_time')::timestamp AS start_time,
    (record_json->'perf'->>'end_time')::timestamp AS end_time,
    -- Calculate latency in seconds
    EXTRACT(EPOCH FROM ((record_json->'perf'->>'end_time')::timestamp - (record_json->'perf'->>'start_time')::timestamp)) AS latency_in_seconds 
FROM 
    raw_data


