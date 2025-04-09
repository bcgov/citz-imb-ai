{% macro extract_dynamic_performance(column, max_calls=5) %}
    -- Get the call count dynamically
    (SELECT LEAST(jsonb_array_length({{ column }}::jsonb->'calls'), {{ max_calls }})) AS call_count,
   
    -- Use a simpler approach that avoids using set-returning functions in aggregates
    {% for i in range(max_calls) %}
        -- Extract function name
        {{ column }}::jsonb->'calls'->{{ i }}->'stack'->1->'method'->>'name' AS function_name_{{ i + 1 }},
        
        -- Extract timestamps
        ({{ column }}::jsonb->'calls'->{{ i }}->'perf'->>'start_time')::TIMESTAMP AS start_time_{{ i + 1 }},
        ({{ column }}::jsonb->'calls'->{{ i }}->'perf'->>'end_time')::TIMESTAMP AS end_time_{{ i + 1 }},
        
        -- Calculate latency directly
        CASE 
            WHEN {{ column }}::jsonb->'calls'->{{ i }}->'perf'->>'start_time' IS NOT NULL 
            AND {{ column }}::jsonb->'calls'->{{ i }}->'perf'->>'end_time' IS NOT NULL
            THEN EXTRACT(epoch FROM 
                (({{ column }}::jsonb->'calls'->{{ i }}->'perf'->>'end_time')::TIMESTAMP - 
                 ({{ column }}::jsonb->'calls'->{{ i }}->'perf'->>'start_time')::TIMESTAMP)
            )
            ELSE NULL
        END AS latency_in_seconds_{{ i + 1 }}
        {% if not loop.last %},{% endif %}
    {% endfor %}
{% endmacro %}