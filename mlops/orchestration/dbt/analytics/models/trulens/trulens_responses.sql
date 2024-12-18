WITH raw_data AS (
    SELECT 
        record_id,
        record_json::json AS record_json
    FROM 
        {{ source('public', 'records') }}  -- Use dbt's source function
)

SELECT 
    record_id,
    {{ unroll_json_to_columns('record_json', 10) }}  -- Replace static SQL with dynamic macro call
FROM 
    raw_data
