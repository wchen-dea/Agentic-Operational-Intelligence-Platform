{{
    config(
        materialized         = 'incremental',
        incremental_strategy = 'merge',
        unique_key           = 'invoice_id',
        file_format          = 'iceberg',
        on_schema_change     = 'sync_all_columns',
        post_hook            = "{{ delete_cdc_rows(ref('bronze_pos_invoices'), 'invoice_id') }}"
    )
}}

with bronze as (
    select * from {{ ref('bronze_pos_invoices') }}
    {% if is_incremental() %}
    where _cdc_ts_ms > (select coalesce(max(_cdc_ts_ms), 0) from {{ this }})
    {% endif %}
),

deduped as (
    select * from (
        select *,
            row_number() over (
                partition by invoice_id
                order by _cdc_ts_ms desc
            ) as rn
        from bronze
        where _cdc_op in ('c', 'u', 'r')
    )
    where rn = 1
)

select
    invoice_id,
    store_id,
    order_id,
    customer_id,
    invoice_type,
    status,
    subtotal,
    tax_amount,
    total_amount,
    refund_amount,
    payment_method,
    -- Derived: net revenue (total minus refunds)
    coalesce(total_amount, 0) - coalesce(refund_amount, 0)  as net_revenue,
    invoiced_at,
    created_at,
    updated_at,
    _cdc_op,
    _cdc_ts_ms,
    _ingested_at
from deduped
