{{
    config(
        materialized  = 'table',
        file_format   = 'iceberg',
        post_hook     = "ANALYZE TABLE {{ this }} COMPUTE STATISTICS"
    )
}}

/*
  Gold: store_realtime_kpis
  ─────────────────────────
  Per-store, per-day KPI aggregation built from the silver CDC layer.
  Replaces the old DELTA-format version.

  Metrics
  -------
  Revenue            total_revenue, avg_order_value
  Appointments       total_appts, show_rate, appt_to_order_conversion
  Invoices           invoice_total, refund_rate, net_revenue
  Work Orders        avg_cycle_time_minutes, overdue_count
  Inventory          sku_count, in_stock_sku_count, in_stock_rate,
                     total_inventory_value, needs_reorder_count
*/

with orders as (

    select
        store_id,
        date(created_at)                            as kpi_date,
        count(*)                                    as order_count,
        sum(total_amount)                           as revenue_total,
        avg(total_amount)                           as avg_order_value,
        sum(discount_amount)                        as discount_total
    from {{ ref('silver_sales_orders') }}
    where status not in ('cancelled', 'void')
    group by store_id, date(created_at)

),

appointments as (

    select
        store_id,
        date(scheduled_at)                          as kpi_date,
        count(*)                                    as appointment_count,
        sum(case when is_show = true  then 1 else 0 end) as show_count,
        round(
            100.0 * sum(case when is_show = true then 1 else 0 end)
            / nullif(count(*), 0), 2
        )                                           as show_rate_pct
    from {{ ref('silver_appointments') }}
    group by store_id, date(scheduled_at)

),

appt_conversions as (

    select
        a.store_id,
        date(a.scheduled_at)                        as kpi_date,
        count(distinct o.order_id)                  as appt_to_order_count
    from {{ ref('silver_appointments') }} a
    left join {{ ref('silver_sales_orders') }} o
        on  a.order_id  = o.order_id
        and a.store_id  = o.store_id
        and date(a.scheduled_at) = date(o.created_at)
    where a.is_show = true
    group by a.store_id, date(a.scheduled_at)

),

invoices as (

    select
        store_id,
        date(invoiced_at)                           as kpi_date,
        count(*)                                    as invoice_count,
        sum(total_amount)                           as invoice_total,
        sum(refund_amount)                          as refund_total,
        sum(net_revenue)                            as net_revenue,
        round(
            100.0 * sum(refund_amount)
            / nullif(sum(total_amount), 0), 2
        )                                           as refund_rate_pct
    from {{ ref('silver_pos_invoices') }}
    where status != 'void'
    group by store_id, date(invoiced_at)

),

work_orders as (

    select
        store_id,
        date(opened_at)                             as kpi_date,
        count(*)                                    as work_order_count,
        avg(cycle_time_minutes)                     as avg_cycle_time_minutes,
        sum(case when is_overdue then 1 else 0 end) as overdue_count
    from {{ ref('silver_work_orders') }}
    group by store_id, date(opened_at)

),

inventory as (

    select
        store_id,
        snapshot_date                               as kpi_date,
        count(distinct sku_id)                      as sku_count,
        sum(case when in_stock = 'true' then 1 else 0 end) as in_stock_sku_count,
        round(
            100.0 * sum(case when in_stock = 'true' then 1 else 0 end)
            / nullif(count(distinct sku_id), 0), 2
        )                                           as in_stock_rate_pct,
        sum(inventory_value)                        as total_inventory_value,
        sum(case when needs_reorder then 1 else 0 end) as needs_reorder_count
    from {{ ref('silver_inventory_snapshots') }}
    group by store_id, snapshot_date

),

-- Spine: all store/date combinations present in any silver table
spine as (

    select store_id, kpi_date from orders
    union
    select store_id, kpi_date from appointments
    union
    select store_id, kpi_date from invoices
    union
    select store_id, kpi_date from work_orders
    union
    select store_id, kpi_date from inventory

)

select
    s.store_id,
    s.kpi_date,

    -- Revenue
    coalesce(o.order_count,           0)            as order_count,
    coalesce(o.revenue_total,         0.0)          as revenue_total,
    coalesce(o.avg_order_value,       0.0)          as avg_order_value,
    coalesce(o.discount_total,        0.0)          as discount_total,

    -- Appointments
    coalesce(a.appointment_count,     0)            as appointment_count,
    coalesce(a.show_count,            0)            as appointment_show_count,
    coalesce(a.show_rate_pct,         0.0)          as appointment_show_rate_pct,
    coalesce(ac.appt_to_order_count,  0)            as appt_to_order_count,
    round(
        100.0 * coalesce(ac.appt_to_order_count, 0)
        / nullif(coalesce(a.appointment_count, 0), 0), 2
    )                                               as appt_conversion_rate_pct,

    -- Invoices
    coalesce(i.invoice_count,         0)            as invoice_count,
    coalesce(i.invoice_total,         0.0)          as invoice_total,
    coalesce(i.refund_total,          0.0)          as refund_total,
    coalesce(i.net_revenue,           0.0)          as net_revenue,
    coalesce(i.refund_rate_pct,       0.0)          as refund_rate_pct,

    -- Work Orders
    coalesce(w.work_order_count,      0)            as work_order_count,
    coalesce(w.avg_cycle_time_minutes, 0.0)         as avg_work_order_cycle_time_minutes,
    coalesce(w.overdue_count,         0)            as overdue_work_order_count,

    -- Inventory
    coalesce(inv.sku_count,           0)            as sku_count,
    coalesce(inv.in_stock_sku_count,  0)            as in_stock_sku_count,
    coalesce(inv.in_stock_rate_pct,   0.0)          as in_stock_rate_pct,
    coalesce(inv.total_inventory_value, 0.0)        as total_inventory_value,
    coalesce(inv.needs_reorder_count, 0)            as needs_reorder_count,

    current_timestamp()                             as updated_at

from spine         s
left join orders   o   on s.store_id = o.store_id   and s.kpi_date = o.kpi_date
left join appointments a on s.store_id = a.store_id  and s.kpi_date = a.kpi_date
left join appt_conversions ac on s.store_id = ac.store_id and s.kpi_date = ac.kpi_date
left join invoices  i  on s.store_id = i.store_id   and s.kpi_date = i.kpi_date
left join work_orders w on s.store_id = w.store_id  and s.kpi_date = w.kpi_date
left join inventory inv on s.store_id = inv.store_id and s.kpi_date = inv.kpi_date
