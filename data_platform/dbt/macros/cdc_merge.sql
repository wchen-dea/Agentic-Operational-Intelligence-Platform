{#
  delete_cdc_rows  —  post-hook macro for silver models.

  Removes rows from the silver Iceberg table whose primary key appears in
  a Debezium DELETE event (_cdc_op = 'd') in the corresponding bronze model.

  Parameters
  ----------
  bronze_model : Relation   e.g. ref('bronze_sales_orders')
  unique_key   : str        primary-key column name

  Usage in a silver model config block:
    {{ config(
        post_hook = "{{ delete_cdc_rows(ref('bronze_sales_orders'), 'order_id') }}"
    ) }}
#}
{% macro delete_cdc_rows(bronze_model, unique_key) %}

DELETE FROM {{ this }}
WHERE {{ unique_key }} IN (
    SELECT {{ unique_key }}
    FROM   {{ bronze_model }}
    WHERE  _cdc_op = 'd'
    {% if is_incremental() %}
    AND    _cdc_ts_ms > (
               SELECT coalesce(max(_cdc_ts_ms), 0) FROM {{ this }}
           )
    {% endif %}
)

{% endmacro %}

