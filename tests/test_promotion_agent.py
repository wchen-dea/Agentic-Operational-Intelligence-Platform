from ai_system.agents.promotion_agent import PromotionAgent


def test_promotion_agent_detects_issues():
    agent = PromotionAgent()
    kpis = {
        "appointment_to_order_conversion_rate": 0.10,
        "appointment_show_rate": 0.50,
        "average_work_order_cycle_time_minutes": 200,
        "branded_revenue_mix_rate": 0.10,
        "pos_invoice_capture_rate": 0.70,
        "inventory_in_stock_rate": 0.80,
        "stockout_sku_count": 10,
    }
    result = agent.run(kpis, context_docs=[])
    signals = result["promotion_signal"]
    assert signals["low_conversion"] is True
    assert signals["low_show_rate"] is True
    assert signals["high_cycle_time"] is True
    assert signals["low_branded_mix"] is True
    assert signals["low_invoice_capture"] is True
    assert signals["low_inventory_in_stock_rate"] is True
    assert signals["high_stockouts"] is True
    assert len(result["recommendations"]) >= 6


def test_promotion_agent_healthy_store():
    agent = PromotionAgent()
    kpis = {
        "appointment_to_order_conversion_rate": 0.45,
        "appointment_show_rate": 0.80,
        "average_work_order_cycle_time_minutes": 60,
        "branded_revenue_mix_rate": 0.35,
        "pos_invoice_capture_rate": 0.95,
        "inventory_in_stock_rate": 0.97,
        "stockout_sku_count": 0,
    }
    result = agent.run(kpis, context_docs=[])
    signals = result["promotion_signal"]
    assert all(v is False for v in signals.values())
    assert result["recommendations"] == ["Maintain current promotion strategy and monitor variance by store segment."]
