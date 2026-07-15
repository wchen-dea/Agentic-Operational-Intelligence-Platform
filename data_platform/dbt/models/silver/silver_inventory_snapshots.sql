{{
    config(
        materialized         = 'incremental',
        incremental_strategy = 'merge',
        unique_key           = ['sku_id', 'store_id', 'snapshot_date'],
        file_format          = 'iceberg',
        on_schema_change     = 'sync_all_columns',
        post_hook            = "{{ delete_cdc_rows(ref('bronze_inventory_snapshots'), 'snapshot_id') }}"
    )
}}

with bronze as (
    select * from {{ ref('bronze_inventory_snapshots') }}
    {% if is_incremental() %}
    where _cdc_ts_ms > (select coalesce(max(_cdc_ts_ms), 0) from {{ this }})
    {% endif %}
),

deduped as (
    select * from (
        select *,
            row_number() over (
                partition by sku_id, store_id, snapshot_date
                order by _cdc_ts_ms desc
            ) as rn
        from bronze
        where _cdc_op in ('c', 'u', 'r')
    )
    where rn = 1
)

select
    snapshot_id,
    sku_id,
    store_id,
    article_id,
    snapshot_date,
    quantity_on_hand,
    quantity_reserved,
    quantity_available,
    reorder_point,
    in_stock,
    unit_cost,
    -- Derived: inventory value
    coalesce(quantity_on_hand, 0) * coalesce(unit_cost, 0)  as inventory_value,
    -- Derived: below reorder point flag
    case
        when coalesce(quantity_available, 0) <= coalesce(reorder_point, 0)
        then true else false
    end                                                     as needs_reorder,
    created_at,
    updated_at,
    _cdc_op,
    _cdc_ts_ms,
    _ingested_at
from deduped
