from ai_layer.agents.orchestrator import AgenticOperationalIntelligenceOrchestrator


def test_orchestrator_answer():
    orchestrator = AgenticOperationalIntelligenceOrchestrator()
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
