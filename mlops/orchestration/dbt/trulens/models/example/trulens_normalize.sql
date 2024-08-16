WITH raw_data AS (
    SELECT 
        record_id,  
        input,
        replace(replace(replace(replace(output, '}"', '}'), '"{', '{'), 'None', '"None"'), '''', '"')::json AS output,
        record_json::json AS record_json
    FROM 
        {{ source('public', 'records') }}  -- Use dbt's source function
), 
parsed_data AS (
    SELECT 
        record_id,
        input,
        output->>'node.ActId' AS node_act_id,
        output->>'score' AS score,
        output,  
        record_json->>'record_id' AS json_record_id,  
        record_json->'app_id'->>'sub_field' AS sub_field  
    FROM 
        raw_data
)

-- Final SELECT statement to retrieve data from the last CTE
SELECT *
FROM parsed_data
