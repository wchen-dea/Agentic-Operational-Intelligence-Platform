{#
  Override dbt's default schema naming to use the custom schema directly
  (without the default `<profile_schema>_<custom_schema>` concatenation).

  In this project, schemas map 1-to-1 to Iceberg namespaces in the REST catalog:
    staging  → iceberg.landing   (Spark-managed landing tables, read-only in dbt)
    bronze   → iceberg.bronze
    silver   → iceberg.silver
    gold     → iceberg.gold
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
