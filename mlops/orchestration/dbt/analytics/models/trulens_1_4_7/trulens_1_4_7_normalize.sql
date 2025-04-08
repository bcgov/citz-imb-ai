{# At the top of your file, use a safer approach to get max_calls #}
{% set max_calls = 5 %}  -- Default to 5 calls
WITH raw_data AS (
    SELECT
        record_id,
        app_id,  
        input,
        output,
        ts,
        record_json::jsonb AS record_json
    FROM
        {{ source('simple', 'trulens_records') }}  -- Use dbt's source function
),
-- Extract all unique performance keys
performance_keys AS (
    SELECT DISTINCT jsonb_object_keys(record_json->'perf') AS perf_key
    FROM raw_data
    WHERE record_json->'perf' IS NOT NULL
),
-- Get app information from trulens_apps table
app_data AS (
    SELECT
        app_id,
        app_name,
        app_version
    FROM
        {{ source('simple', 'trulens_apps') }}
),
parsed_data AS (
    SELECT
        rd.record_id,
        rd.input,
        rd.ts,
        rd.record_json->'calls'->2->'rets' AS LLM_output,
        {{ unroll_json_to_columns('rd.record_json', 10) }},  -- Replace static SQL with dynamic macro call
        rd.record_json->>'record_id' AS json_record_id,  
        rd.record_json->'app_id' AS app_id_json,
        rd.app_id AS app_id_raw,
        app.app_name,
        app.app_version,
        (rd.record_json->'perf'->>'start_time')::timestamp AS start_time,
        (rd.record_json->'perf'->>'end_time')::timestamp AS end_time,
        -- Calculate latency in seconds
        EXTRACT(EPOCH FROM ((rd.record_json->'perf'->>'end_time')::timestamp - (rd.record_json->'perf'->>'start_time')::timestamp)) AS latency,
        -- Fully dynamic performance extraction
        {{ extract_dynamic_performance('rd.record_json', max_calls) }}
    FROM
        raw_data rd
    LEFT JOIN
        app_data app
    ON 
        rd.app_id = app.app_id
),
feedback_data AS (
    SELECT
        record_id,
        array_agg(result) AS result  -- Replace this with actual column names in feedbacks
    FROM
        {{ source('simple', 'trulens_feedbacks') }}  -- Join feedbacks table
    GROUP BY
        record_id  -- Group by record_id to aggregate feedbacks
),
reasons_extraction AS (
    SELECT
        record_id,
        array_agg(call_element->'meta'->>'reason') FILTER (WHERE call_element->'meta'->>'reason' IS NOT NULL) AS reason_comments
    FROM
        {{ source('simple', 'trulens_feedbacks') }},
        jsonb_array_elements(calls_json::jsonb->'calls') AS call_element
    GROUP BY record_id
)
-- Final SELECT statement to retrieve data from the last CTE
-- SELECT *
-- FROM parsed_data
-- Final join to merge parsed_data with feedback_data based on record_id hash
SELECT
    pd.*,
    fb.result,  -- Include feedback details
    re.reason_comments -- Include extracted reasons
FROM
    parsed_data pd
LEFT JOIN
    feedback_data fb
    ON pd.record_id = fb.record_id
LEFT JOIN
    reasons_extraction re
    ON pd.record_id = re.record_id