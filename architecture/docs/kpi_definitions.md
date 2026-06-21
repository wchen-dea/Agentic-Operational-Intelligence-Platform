# KPI Definitions

Target status: `agentic-operational-intelligence-platform`

These KPIs represent the cross-domain operational view used by the agentic recommendation and alerting layers. All 16 KPIs are defined in the machine-readable catalog at `data_platform/kpi_catalog.yaml` with unit, direction, thresholds, and descriptions.

The typed semantic layer (`data_platform/semantic_layer.py`) wraps raw KPI values with `KPIRecord` objects that include anomaly detection, LLM-ready summaries, and provenance metadata. The queryable data store (`data_platform/kpi_store.py`) provides a SQLite-backed `KPIDataSource` protocol.

Primary source assumption: sales-order, appointment, POS-invoice, and work-order events are derived from AWS Aurora MySQL transactions or CDC streams.

## Sales KPIs

| KPI | Unit | Direction | Description |
|-----|------|-----------|-------------|
| `revenue_total` | USD | higher_is_better | Total revenue from completed sales orders |
| `order_count` | count | higher_is_better | Number of completed sales orders |
| `average_order_value` | USD | higher_is_better | Average revenue per completed order |
| `conversion_rate` | ratio | higher_is_better | Fraction of opportunities converted to orders |

Typical source tables: Aurora MySQL sales-order headers and line items

## Appointment KPIs

| KPI | Unit | Direction | Description |
|-----|------|-----------|-------------|
| `appointment_count` | count | higher_is_better | Total scheduled appointments |
| `appointment_show_rate` | ratio | higher_is_better | Fraction of appointments where the customer appeared |
| `appointment_to_order_conversion_rate` | ratio | higher_is_better | Fraction of appointments that resulted in a sales order |

Typical source tables: Aurora MySQL appointment bookings, check-ins, and completion status

## POS KPIs

| KPI | Unit | Direction | Description |
|-----|------|-----------|-------------|
| `invoice_count` | count | higher_is_better | Number of POS invoices generated |
| `invoice_total` | USD | higher_is_better | Total invoiced revenue |
| `refund_rate` | ratio | lower_is_better | Fraction of transactions that were refunded |

Typical source tables: Aurora MySQL POS invoice headers, tenders, and refund records

## Inventory KPIs

| KPI | Unit | Direction | Description |
|-----|------|-----------|-------------|
| `inventory_in_stock_rate` | ratio | higher_is_better | Fraction of SKUs currently in stock |
| `low_stock_sku_count` | count | lower_is_better | Number of SKUs below reorder threshold |
| `stockout_sku_count` | count | lower_is_better | Number of SKUs with zero available inventory |

## Work Order KPIs

| KPI | Unit | Direction | Description |
|-----|------|-----------|-------------|
| `work_order_count` | count | neutral | Total work orders in the current period |
| `average_cycle_time_minutes` | minutes | lower_is_better | Average time from work order creation to completion |
| `overdue_work_order_count` | count | lower_is_better | Number of work orders past their SLA target |

Typical source tables: Aurora MySQL work-order lifecycle and service status records

## Promotion KPIs

| KPI | Unit | Direction | Description |
|-----|------|-----------|-------------|
| `branded_revenue_mix_rate` | ratio | higher_is_better | Fraction of revenue from branded products |

Additional promotion metrics (computed but not yet in the KPI catalog):

- `promo_revenue_lift_pct`
- `promo_conversion_lift_pct`
- `promo_margin_impact_pct`

## Alert thresholds

All KPIs have configurable alert thresholds defined in `alerts/rules/kpi_thresholds.yaml`. Each rule includes severity, direction, description, unit, and remediation guidance. The alert engine (`alerts/engine.py`) evaluates KPIs against these rules and produces enriched alert objects.
