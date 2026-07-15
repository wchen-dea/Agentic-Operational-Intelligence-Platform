{{
    config(
        materialized  = 'table',
        file_format   = 'iceberg',
        schema        = 'analytics'
    )
}}

/*
  analytics.feat_customer_behavior
  ──────────────────────────────────
  Customer-grain feature table for churn prediction and LTV modeling.
  Aggregates silver CDC tables into behavioral signals per customer.

  Grain        : one row per customer_id (latest snapshot)
  Feature groups:
    purchase_*   — recency / frequency / monetary (RFM) signals
    appointment_*— booking cadence and show-rate history
    invoice_*    — payment patterns and refund history
*/

with orders as (
    select
        customer_id,
        max(created_at)                                         as last_order_date,
        count(*)                                                as total_orders,
        sum(total_amount)                                       as total_revenue,
        avg(total_amount)                                       as avg_order_value,
        sum(discount_amount)                                    as total_discounts,
        count(distinct store_id)                                as stores_visited,
        -- Recency: days since last order
        datediff(current_date(), max(cast(created_at as date))) as days_since_last_order,
        -- Frequency bucket (RFM)
        case
            when count(*) >= 10 then 'high'
            when count(*) >= 3  then 'medium'
            else 'low'
        end                                                     as purchase_frequency_band
    from {{ ref('silver_sales_orders') }}
    where status not in ('cancelled', 'void')
    group by customer_id
),

appointments as (
    select
        customer_id,
        count(*)                                                as total_appointments,
        sum(case when is_show = true  then 1 else 0 end)        as total_shows,
        sum(case when is_show = false then 1 else 0 end)        as total_no_shows,
        round(
            100.0 * sum(case when is_show = true then 1 else 0 end)
            / nullif(count(*), 0), 2
        )                                                       as show_rate_pct,
        max(scheduled_at)                                       as last_appointment_date,
        datediff(current_date(), max(cast(scheduled_at as date))) as days_since_last_appt
    from {{ ref('silver_appointments') }}
    group by customer_id
),

invoices as (
    select
        customer_id,
        count(*)                                                as total_invoices,
        sum(total_amount)                                       as total_invoiced,
        sum(refund_amount)                                      as total_refunded,
        round(
            100.0 * sum(refund_amount)
            / nullif(sum(total_amount), 0), 2
        )                                                       as refund_rate_pct,
        count(case when refund_amount > 0 then 1 end)           as refund_event_count
    from {{ ref('silver_pos_invoices') }}
    group by customer_id
)

select
    coalesce(o.customer_id, a.customer_id, i.customer_id)       as customer_id,

    -- Purchase features
    coalesce(o.last_order_date,     null)                        as last_order_date,
    coalesce(o.total_orders,         0)                          as purchase_count,
    coalesce(o.total_revenue,        0.0)                        as purchase_revenue_total,
    coalesce(o.avg_order_value,      0.0)                        as purchase_avg_order_value,
    coalesce(o.total_discounts,      0.0)                        as purchase_discount_total,
    coalesce(o.stores_visited,       0)                          as stores_visited,
    coalesce(o.days_since_last_order, 9999)                      as days_since_last_order,
    coalesce(o.purchase_frequency_band, 'none')                  as purchase_frequency_band,

    -- Appointment features
    coalesce(a.total_appointments,    0)                         as appointment_count,
    coalesce(a.total_shows,           0)                         as appointment_show_count,
    coalesce(a.total_no_shows,        0)                         as appointment_no_show_count,
    coalesce(a.show_rate_pct,         0.0)                       as appointment_show_rate_pct,
    coalesce(a.days_since_last_appt,  9999)                      as days_since_last_appointment,

    -- Invoice / payment features
    coalesce(i.total_invoices,        0)                         as invoice_count,
    coalesce(i.total_invoiced,        0.0)                       as invoice_total,
    coalesce(i.total_refunded,        0.0)                       as refund_total,
    coalesce(i.refund_rate_pct,       0.0)                       as refund_rate_pct,
    coalesce(i.refund_event_count,    0)                         as refund_event_count,

    -- Churn risk signal (simple heuristic; replace with ML model score)
    case
        when coalesce(o.days_since_last_order, 9999) > 90
         and coalesce(a.days_since_last_appt,  9999) > 90
        then 'high'
        when coalesce(o.days_since_last_order, 9999) > 30
        then 'medium'
        else 'low'
    end                                                          as churn_risk_band,

    current_timestamp()                                          as feature_ts

from orders     o
full outer join appointments a on o.customer_id = a.customer_id
full outer join invoices      i on coalesce(o.customer_id, a.customer_id) = i.customer_id
where coalesce(o.customer_id, a.customer_id, i.customer_id) is not null
