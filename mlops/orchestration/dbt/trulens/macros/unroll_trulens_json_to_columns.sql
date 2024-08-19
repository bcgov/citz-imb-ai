{% macro unroll_json_to_columns(column, max_elements) %}
    {%- for i in range(max_elements) %}
        record_json->'calls'->0->'rets'->{{ i }}->'text' AS response_{{ i+1 }}_text,
        record_json->'calls'->0->'rets'->{{ i }}->'node.ActId' AS response_{{ i+1 }}_act_id,
        record_json->'calls'->0->'rets'->{{ i }}->'Regulations' AS response_{{ i+1 }}_regulations,
        record_json->'calls'->0->'rets'->{{ i }}->'node.sectionId' AS response_{{ i+1 }}_section_id,
        record_json->'calls'->0->'rets'->{{ i }}->'node.sectionName' AS response_{{ i+1 }}_section_name,
        record_json->'calls'->0->'rets'->{{ i }}->'node.url' AS response_{{ i+1 }}_url
        {%- if not loop.last %}, {% endif %}
    {%- endfor %}
{% endmacro %}
