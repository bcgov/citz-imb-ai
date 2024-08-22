{% macro extract_performance(
        column,
        max_elements
    ) %}
    {%- for i in range(max_elements) %}
            (record_json->'calls'->{{ i }}->'perf'->>'start_time')::TIMESTAMP AS start_time_{{ i + 1 }},
            (record_json->'calls'->{{ i }}->'perf'->>'end_time')::TIMESTAMP AS end_time_{{ i + 1 }},
            EXTRACT(epoch FROM ((record_json->'calls'->{{ i }}->'perf'->>'end_time')::TIMESTAMP - (record_json->'calls'->{{ i }}->'perf'->>'start_time')::TIMESTAMP)) AS latency_in_seconds_{{ i + 1 }}
        {%- if not loop.last %},
        {% endif %}
    {%- endfor %}
{% endmacro %}
