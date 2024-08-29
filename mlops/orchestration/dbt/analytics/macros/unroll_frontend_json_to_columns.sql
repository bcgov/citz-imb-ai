{% macro unroll_frontend_json_to_columns(json_column, max_responses) %}
    {% for i in range(1, max_responses + 1) %}
        ({{ json_column }}->{{ i - 1 }}->>'clicks')::int AS response_{{ i }}_clicks,
        NULLIF({{ json_column }}->{{ i - 1 }}->>'lastClickTimestamp', '')::timestamp AS response_{{ i }}_last_click_timestamp
        {%- if not loop.last %},{% endif %}
    {% endfor %}
{% endmacro %}
