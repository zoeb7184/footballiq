{# Bronze is append-only; silver reads only the newest load of each source. #}
{% macro latest_load(source_file) %}
    _load_id = (
        select load_id
        from {{ source('bronze', '_loads') }}
        where source_file = '{{ source_file }}'
        order by ingested_at desc
        limit 1
    )
{% endmacro %}
