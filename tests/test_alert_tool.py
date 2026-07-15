from ai_layer.agents.tools.alert_tool import load_rules, detect_kpi_alerts_for_store


def test_load_rules_valid_path():
    from config.settings import settings

    rules = load_rules(settings.alert_rules_path)
    assert "thresholds" in rules
    assert "revenue_total" in rules["thresholds"]
    assert rules["thresholds"]["revenue_total"]["min"] == 1000


def test_load_rules_missing_file():
    rules = load_rules("/nonexistent/path/rules.yaml")
    assert rules == {"thresholds": {}}


def test_detect_kpi_alerts_for_store():
    from config.settings import settings

    kpis = {
        "store_id": "999",
        "revenue_total": 500,
        "appointment_show_rate": 0.50,
        "pos_invoice_capture_rate": 0.70,
        "inventory_in_stock_rate": 0.80,
        "stockout_sku_count": 10,
        "average_work_order_cycle_time_minutes": 200,
        "overdue_work_order_count": 8,
    }
    alerts = detect_kpi_alerts_for_store(kpis, settings.alert_rules_path)
    metrics_alerted = [a["metric"] for a in alerts]
    assert "revenue_total" in metrics_alerted
    assert "appointment_show_rate" in metrics_alerted
    assert "stockout_sku_count" in metrics_alerted
    assert "average_work_order_cycle_time_minutes" in metrics_alerted
    assert all(a["store_id"] == "999" for a in alerts)
