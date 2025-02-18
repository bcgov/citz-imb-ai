{{ config(materialized='view') }}

SELECT
    fa.*,
    tn.input,
    tn.app_id,
    tn.LLM_output,
    tn.feedback_score,
    tn.user_comment,
    tn.vote_type,
    tn.feedback_timestamp,
    tn.json_record_id,
    tn.start_time,
    tn.end_time,
    tn.latency_in_seconds,
    {{ dbt_utils.star(from=ref('trulens_normalize'), except=[
        'record_id', 
        'input', 
        'app_id', 
        'LLM_output', 
        'json_record_id', 
        'start_time', 
        'end_time', 
        'latency_in_seconds',
        'feedback_score',
        'user_comment',
        'vote_type',
        'feedback_timestamp'
    ]) }}
FROM {{ ref('normalized_analytics') }} fa
LEFT JOIN {{ ref('trulens_normalize') }} tn
    ON fa.record_id = tn.record_id
