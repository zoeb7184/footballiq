{# Use custom schema names verbatim (silver/gold), not dbt's default
   "<target>_<custom>" prefixing — layers are fixed namespaces here. #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
