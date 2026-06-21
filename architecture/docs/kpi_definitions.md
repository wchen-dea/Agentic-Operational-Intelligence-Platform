# KPI Definitions

Target status: `agentic-operational-intelligence-platform`

These KPIs represent the cross-domain operational view used by the agentic recommendation and alerting layers.

Primary source assumption: sales-order, appointment, POS-invoice, and work-order events are derived from AWS Aurora MySQL transactions or CDC streams.

## Sales KPIs

- revenue_total
- order_count
- average_order_value
- conversion_rate
- Typical source tables: Aurora MySQL sales-order headers and line items

## Appointment KPIs

- appointment_count
- appointment_show_rate
- appointment_to_order_conversion_rate
- Typical source tables: Aurora MySQL appointment bookings, check-ins, and completion status

## POS KPIs

- invoice_count
- invoice_total
- refund_rate
- pos_invoice_capture_rate
- Typical source tables: Aurora MySQL POS invoice headers, tenders, and refund records

## Inventory KPIs

- inventory_in_stock_rate
- low_stock_sku_count
- stockout_sku_count
- inventory_turnover_proxy

## Work Order KPIs

- work_order_count
- average_cycle_time_minutes
- overdue_work_order_count
- Typical source tables: Aurora MySQL work-order lifecycle and service status records

## Promotion KPIs

- promo_revenue_lift_pct
- promo_conversion_lift_pct
- promo_margin_impact_pct
- branded_revenue_mix_rate
