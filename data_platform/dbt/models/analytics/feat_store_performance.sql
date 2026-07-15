{{
    config(
        materialized  = 'table',
        file_format   = 'iceberg',
        schema        = 'analytics',
        post_hook     = "ANALYZE TABLE {{ this }} COMPUTE STATISTICS"
    )
}}

/*
  analytics.feat_store_performance
  ─────────────────────────────────
  Per-store ML feature table derived from gold KPIs.
  Includes rolling windows (7d, 28d), lag features, and ratio deltas
  that capture momentum signals for revenue forecasting and anomaly detection.

  Grain        : one row per (store_id, kpi_date)
  Feature groups:
    revenue_*    — trailing revenue windows and WoW/MoM growth rates
    appointment_*— show-rate trajectory and conversion trends
    work_order_* — cycle-time volatility and backlog signals
    inventory_*  — stock-out risk and reorder pressure
*/

with kpis as (
    select * from {{ ref('gold_store_kpis') }}
),

rolling as (
    select
        store_id,
        kpi_date,

        -- ── Revenue features ─────────────────────────────────────────
        revenue_total,
        avg_order_value,
        discount_total,

        avg(revenue_total) over (
            partition by store_id
            order by kpi_date
            rows between 6 preceding and current row
        )                                               as revenue_7d_avg,

        avg(revenue_total) over (
            partition by store_id
            order by kpi_date
            rows between 27 preceding and current row
        )                                               as revenue_28d_avg,

        sum(revenue_total) over (
            partition by store_id
            order by kpi_date
            rows between 6 preceding and current row
        )                                               as revenue_7d_sum,

        -- WoW growth rate
        round(
            (revenue_total - lag(revenue_total, 7) over (
                partition by store_id order by kpi_date))
            / nullif(lag(revenue_total, 7) over (
                partition by store_id order by kpi_date), 0),
            4
        )                                               as revenue_wow_growth,

        -- MoM growth rate
        round(
            (revenue_total - lag(revenue_total, 28) over (
                partition by store_id order by kpi_date))
            / nullif(lag(revenue_total, 28) over (
                partition by store_id order by kpi_date), 0),
            4
        )                                               as revenue_mom_growth,

        -- Revenue volatility (std dev over 7d)
        stddev(revenue_total) over (
            partition by store_id
            order by kpi_date
            rows between 6 preceding and current row
        )                                               as revenue_7d_stddev,

        -- ── Appointment features ──────────────────────────────────────
        appointment_count,
        appointment_show_rate_pct,
        appt_conversion_rate_pct,

        avg(appointment_show_rate_pct) over (
            partition by store_id
            order by kpi_date
            rows between 6 preceding and current row
        )                                               as show_rate_7d_avg,

        avg(appt_conversion_rate_pct) over (
            partition by store_id
            order by kpi_date
            rows between 6 preceding and current row
        )                                               as conversion_rate_7d_avg,

        -- Show rate delta (today vs 7d avg)
        appointment_show_rate_pct - avg(appointment_show_rate_pct) over (
            partition by store_id
            order by kpi_date
            rows between 6 preceding and current row
        )                                               as show_rate_delta_vs_7d,

        -- ── Work order features ───────────────────────────────────────
        work_order_count,
        avg_work_order_cycle_time_minutes,
        overdue_work_order_count,

        avg(avg_work_order_cycle_time_minutes) over (
            partition by store_id
            order by kpi_date
            rows between 6 preceding and current row
        )                                               as cycle_time_7d_avg,

        -- Overdue rate (fraction of open WOs that are overdue)
        round(
            overdue_work_order_count * 1.0
            / nullif(work_order_count, 0),
            4
        )                                               as overdue_rate,

        -- Backlog signal: WoW change in overdue count
        overdue_work_order_count
            - lag(overdue_work_order_count, 7) over (
                partition by store_id order by kpi_date)
                                                        as overdue_wow_delta,

        -- ── Inventory features ────────────────────────────────────────
        sku_count,
        in_stock_rate_pct,
        total_inventory_value,
        needs_reorder_count,

        avg(in_stock_rate_pct) over (
            partition by store_id
            order by kpi_date
            rows between 6 preceding and current row
        )                                               as in_stock_rate_7d_avg,

        -- Stock-out pressure: reorder count / total SKUs
        round(
            needs_reorder_count * 1.0
            / nullif(sku_count, 0),
            4
        )                                               as reorder_pressure_rate,

        current_timestamp()                             as feature_ts

    from kpis
)

select * from rolling
