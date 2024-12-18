SELECT 
    record_id,
    array_agg(result) AS result,
    array_agg(comment) AS comment,
    array_agg(CASE 
        WHEN result = 1 THEN 'up_vote'
        WHEN result = -1 THEN 'down_vote'
        ELSE 'no_vote'
    END) AS vote_type,
    array_agg(result::float) AS feedback_score,
    array_agg(created_at) AS feedback_timestamp
FROM 
    {{ source('public', 'feedbacks') }}
GROUP BY 
    record_id

