-- Final SELECT statement to retrieve data from the last CTE
-- SELECT *
-- FROM parsed_data

-- Final join to merge all trulens data together
-- ref() functions guarantee that prerequisite tables are built first
SELECT 
    tb.*,
    tt.*,
    tr.*,
    tf.*
FROM 
    {{ref('trulens_base')}} tb
LEFT JOIN 
    {{ref('trulens_timings')}} tt ON tb.record_id = tt.record_id
LEFT JOIN 
    {{ref('trulens_responses')}} tr ON tb.record_id = tr.record_id
LEFT JOIN 
    {{ref('trulens_feedback')}} tf ON tb.record_id = tf.record_id;
