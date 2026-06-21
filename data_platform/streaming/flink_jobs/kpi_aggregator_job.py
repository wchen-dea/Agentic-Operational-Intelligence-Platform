"""
Sample streaming KPI aggregator.

This is framework-neutral sample logic. In production, wire this into:
- PyFlink DataStream/Table API
- Databricks Structured Streaming
- Spark/Flink SQL jobs
"""
from __future__ import annotations
from collections import defaultdict
from typing import Iterable, Dict, Any


def aggregate_kpis(events: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Aggregate basic KPIs by store_id from mixed retail events."""
    state = defaultdict(lambda: {
        "revenue_total": 0.0,
        "order_count": 0,
        "branded_order_revenue": 0.0,
        "appointment_count": 0,
        "appointment_show_count": 0,
        "invoice_total": 0.0,
        "invoice_count": 0,
        "branded_invoice_total": 0.0,
        "refund_count": 0,
        "work_order_count": 0,
        "work_order_cycle_time_total": 0.0,
        "overdue_work_order_count": 0,
        "inventory_sku_count": 0,
        "in_stock_sku_count": 0,
        "low_stock_sku_count": 0,
        "stockout_sku_count": 0,
    })

    for event in events:
        store_id = str(event.get("store_id", "UNKNOWN"))
        event_type = event.get("event_type")
        s = state[store_id]

        if event_type == "sales_order":
            if event.get("status") in {"completed", "fulfilled", "paid"}:
                order_amount = float(event.get("order_amount", 0.0))
                s["revenue_total"] += order_amount
                s["order_count"] += 1
                if event.get("brand_tier") == "branded":
                    s["branded_order_revenue"] += order_amount

        elif event_type == "appointment":
            s["appointment_count"] += 1
            if event.get("status") in {"showed", "completed"}:
                s["appointment_show_count"] += 1

        elif event_type == "pos_invoice":
            invoice_amount = float(event.get("invoice_amount", 0.0))
            s["invoice_total"] += invoice_amount
            s["invoice_count"] += 1
            if event.get("refund_flag"):
                s["refund_count"] += 1
            if event.get("brand_tier") == "branded":
                s["branded_invoice_total"] += invoice_amount

        elif event_type == "inventory_snapshot":
            s["inventory_sku_count"] = int(event.get("sku_count", s["inventory_sku_count"]))
            s["in_stock_sku_count"] = int(event.get("in_stock_sku_count", s["in_stock_sku_count"]))
            s["low_stock_sku_count"] = int(event.get("low_stock_sku_count", s["low_stock_sku_count"]))
            s["stockout_sku_count"] = int(event.get("stockout_sku_count", s["stockout_sku_count"]))

        elif event_type == "work_order":
            s["work_order_count"] += 1
            s["work_order_cycle_time_total"] += float(event.get("cycle_time_minutes", 0.0))
            if event.get("status") == "overdue":
                s["overdue_work_order_count"] += 1

    output = {}
    for store_id, s in state.items():
        order_count = s["order_count"]
        appointment_count = s["appointment_count"]
        invoice_count = s["invoice_count"]
        work_order_count = s["work_order_count"]

        output[store_id] = {
            **s,
            "average_order_value": s["revenue_total"] / order_count if order_count else 0.0,
            "appointment_show_rate": s["appointment_show_count"] / appointment_count if appointment_count else 0.0,
            "appointment_to_order_conversion_rate": order_count / appointment_count if appointment_count else 0.0,
            "refund_rate": s["refund_count"] / invoice_count if invoice_count else 0.0,
            "average_work_order_cycle_time_minutes": s["work_order_cycle_time_total"] / work_order_count if work_order_count else 0.0,
            "pos_invoice_capture_rate": invoice_count / order_count if order_count else 0.0,
            "inventory_in_stock_rate": s["in_stock_sku_count"] / s["inventory_sku_count"] if s["inventory_sku_count"] else 0.0,
            "inventory_turnover_proxy": order_count / s["inventory_sku_count"] if s["inventory_sku_count"] else 0.0,
            "branded_revenue_mix_rate": (
                (s["branded_order_revenue"] + s["branded_invoice_total"]) /
                (s["revenue_total"] + s["invoice_total"])
            ) if (s["revenue_total"] + s["invoice_total"]) else 0.0,
        }
    return output


if __name__ == "__main__":
    sample = [
        {"event_type": "sales_order", "store_id": "245", "order_amount": 700, "status": "completed"},
        {"event_type": "appointment", "store_id": "245", "status": "showed"},
        {"event_type": "pos_invoice", "store_id": "245", "invoice_amount": 695, "refund_flag": False},
        {"event_type": "work_order", "store_id": "245", "cycle_time_minutes": 91, "status": "completed"},
    ]
    print(aggregate_kpis(sample))
