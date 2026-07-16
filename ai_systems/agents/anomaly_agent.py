from typing import Any

from ai_systems.tools.alert_tool import detect_kpi_alerts_for_store


class AnomalyAgent:
    def __init__(self, rules_path: str):
        self.rules_path = rules_path

    def run(self, kpis: dict[str, Any]) -> list[dict[str, Any]]:
        if "store_id" not in kpis:
            return []
        return detect_kpi_alerts_for_store(kpis, self.rules_path)
