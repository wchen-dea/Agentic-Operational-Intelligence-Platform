from __future__ import annotations
from typing import Dict, Any

# Mock KPI source. Replace with Delta SQL, Databricks SQL Warehouse, Feature Store, or a serving API.
SAMPLE_KPIS = {
    "245": {
        "store_id": "245",
        "region": "Phoenix",
        "revenue_total": 820.0,
        "order_count": 9,
        "average_order_value": 91.1,
        "appointment_show_rate": 0.58,
        "appointment_to_order_conversion_rate": 0.21,
        "invoice_total": 790.0,
        "pos_invoice_capture_rate": 0.78,
        "refund_rate": 0.03,
        "inventory_in_stock_rate": 0.84,
        "low_stock_sku_count": 18,
        "stockout_sku_count": 6,
        "inventory_turnover_proxy": 0.13,
        "branded_revenue_mix_rate": 0.16,
        "average_work_order_cycle_time_minutes": 145.0,
        "overdue_work_order_count": 7,
    },
    "101": {
        "store_id": "101",
        "region": "Phoenix",
        "revenue_total": 4300.0,
        "order_count": 41,
        "average_order_value": 104.9,
        "appointment_show_rate": 0.78,
        "appointment_to_order_conversion_rate": 0.39,
        "invoice_total": 4200.0,
        "pos_invoice_capture_rate": 0.94,
        "refund_rate": 0.02,
        "inventory_in_stock_rate": 0.95,
        "low_stock_sku_count": 5,
        "stockout_sku_count": 1,
        "inventory_turnover_proxy": 0.31,
        "branded_revenue_mix_rate": 0.29,
        "average_work_order_cycle_time_minutes": 82.0,
        "overdue_work_order_count": 1,
    },
}


def fetch_store_kpis(store_id: str | None = None, region: str | None = None) -> Dict[str, Any]:
    if store_id and store_id in SAMPLE_KPIS:
        return SAMPLE_KPIS[store_id]
    if region:
        region_rows = [v for v in SAMPLE_KPIS.values() if v.get("region") == region]
        if not region_rows:
            return {}
        return {
            "region": region,
            "store_count": len(region_rows),
            "revenue_total": sum(x["revenue_total"] for x in region_rows),
            "order_count": sum(x["order_count"] for x in region_rows),
            "overdue_work_order_count": sum(x["overdue_work_order_count"] for x in region_rows),
            "average_appointment_show_rate": sum(x["appointment_show_rate"] for x in region_rows) / len(region_rows),
            "average_appointment_to_order_conversion_rate": sum(x["appointment_to_order_conversion_rate"] for x in region_rows) / len(region_rows),
            "average_pos_invoice_capture_rate": sum(x["pos_invoice_capture_rate"] for x in region_rows) / len(region_rows),
            "average_inventory_in_stock_rate": sum(x["inventory_in_stock_rate"] for x in region_rows) / len(region_rows),
            "stockout_sku_count": sum(x["stockout_sku_count"] for x in region_rows),
            "average_branded_revenue_mix_rate": sum(x["branded_revenue_mix_rate"] for x in region_rows) / len(region_rows),
        }
    return {"stores": list(SAMPLE_KPIS.values())}
