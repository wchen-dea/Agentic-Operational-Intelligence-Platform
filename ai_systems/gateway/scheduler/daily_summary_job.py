from ai_system.orchestration.orchestrator import get_orchestrator


def build_daily_summary(region: str = "Phoenix") -> str:
    orchestrator = get_orchestrator()
    result = orchestrator.answer(
        question="Summarize operational KPI performance and promotion recommendations for executives.",
        region=region,
    )
    return result["answer"]


if __name__ == "__main__":
    print(build_daily_summary())
