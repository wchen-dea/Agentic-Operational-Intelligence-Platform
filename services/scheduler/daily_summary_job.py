from ai_layer.agents.orchestrator import AgenticOperationalIntelligenceOrchestrator


def build_daily_summary(region: str = "Phoenix") -> str:
    orchestrator = AgenticOperationalIntelligenceOrchestrator()
    result = orchestrator.answer(
        question="Summarize operational KPI performance and promotion recommendations for executives.",
        region=region,
    )
    return result["answer"]


if __name__ == "__main__":
    print(build_daily_summary())
