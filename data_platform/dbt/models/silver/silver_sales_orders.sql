{{
    config(
        materialized         = 'incremental',
        incremental_strategy = 'merge',
        unique_key           = 'order_id',
        file_format          = 'iceberg',
        on_schema_change     = 'sync_all_columns',
        post_hook            = "{{ delete_cdc_rows(ref('bronze_sales_orders'), 'order_id') }}"
    )
}}

/*
  Silver: sales_orders
  ────────────────────
  Current state of every sales order.  Applies CDC merge from bronze:
    - INSERT / UPDATE  → upsert by order_id
    - DELETE           → row removed via post_hook

  Only the latest version of each order (by cdc_ts_ms) is kept.
*/

with bronze as (

    select * from {{ ref('bronze_sales_orders') }}

    {% if is_incremental() %}
    where _cdc_ts_ms > (
        select coalesce(max(_cdc_ts_ms), 0) from {{ this }}
    )
    {% endif %}

),

-- Deduplicate: keep the latest event per order in this batch
deduped as (

    select *
    from (
        select
            *,
            row_number() over (
                partition by order_id
                order by _cdc_ts_ms desc
            ) as rn
        from bronze
        where _cdc_op in ('c', 'u', 'r')   -- deletes handled by post_hook
    )
    where rn = 1

)

select
    order_id,
    store_id,
    customer_id,
    status,
    order_type,
    total_amount,
    tax_amount,
    discount_amount,
    currency_code,
    promotion_id,
    sales_rep_id,
    created_at,
    updated_at,
    _cdc_op,
    _cdc_ts_ms,
    _ingested_at
from deduped
