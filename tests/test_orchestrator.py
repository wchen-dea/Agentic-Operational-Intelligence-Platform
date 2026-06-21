from ai_layer.agents.orchestrator import Orchestrator


def test_orchestrator_answer():
    orchestrator = Orchestrator()
    result = orchestrator.answer(
        "Why are sales down and what should we do?",
        store_id="245",
        region="Phoenix",
        persona="executive",
    )
    assert "answer" in result
    assert result["kpis"]["store_id"] == "245"
    assert len(result["retrieved_context"]) > 0
    assert "operational_brief" in result
    assert result["persona"] == "executive"
    assert "Strategic playbook" in result["answer"]


def test_orchestrator_region_scope():
    orchestrator = Orchestrator()
    result = orchestrator.answer(
        "Regional performance summary",
        region="Phoenix",
        persona="executive",
    )
    assert result["kpis"]["region"] == "Phoenix"
    assert "appointment_show_rate" in result["kpis"]
    assert "appointment_to_order_conversion_rate" in result["kpis"]
    assert len(result["promotion_analysis"]["recommendations"]) > 0


def test_orchestrator_operational_brief():
    orchestrator = Orchestrator()
    result = orchestrator.get_operational_brief(store_id="245", persona="store_manager")
    assert "operational_brief" in result
    assert result["persona"] == "store_manager"
    brief = result["operational_brief"]
    assert "priority_actions" in brief
    assert "diagnosis" in brief
