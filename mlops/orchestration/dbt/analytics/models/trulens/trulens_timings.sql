WITH raw_data AS (
    SELECT 
        record_id,
        record_json::json AS record_json
    FROM 
        {{ source('public', 'records') }}  -- Use dbt's source function
)

SELECT 
    record_id,
    {{ extract_performance('record_json', 4) }}  -- Replace static SQL with dynamic macro call
FROM 
    raw_data
