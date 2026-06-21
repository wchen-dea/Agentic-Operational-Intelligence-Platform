from data_platform.streaming.flink_jobs.kpi_aggregator_job import aggregate_kpis


def test_aggregate_kpis():
    events = [
        {"event_type": "sales_order", "store_id": "245", "order_amount": 100, "status": "completed", "brand_tier": "branded"},
        {"event_type": "sales_order", "store_id": "245", "order_amount": 200, "status": "completed"},
        {"event_type": "appointment", "store_id": "245", "status": "showed"},
        {"event_type": "appointment", "store_id": "245", "status": "no_show"},
        {"event_type": "pos_invoice", "store_id": "245", "invoice_amount": 280, "refund_flag": False, "brand_tier": "branded"},
        {"event_type": "inventory_snapshot", "store_id": "245", "sku_count": 100, "in_stock_sku_count": 93, "low_stock_sku_count": 5, "stockout_sku_count": 2},
    ]
    result = aggregate_kpis(events)
    assert result["245"]["revenue_total"] == 300
    assert result["245"]["order_count"] == 2
    assert result["245"]["average_order_value"] == 150
    assert result["245"]["appointment_show_rate"] == 0.5
    assert result["245"]["pos_invoice_capture_rate"] == 0.5
    assert result["245"]["inventory_in_stock_rate"] == 0.93
    assert result["245"]["stockout_sku_count"] == 2
    assert round(result["245"]["branded_revenue_mix_rate"], 4) == round((100 + 280) / (300 + 280), 4)
