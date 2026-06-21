from __future__ import annotations
from typing import Dict, Any, List
from ai_layer.agents.tools.alert_tool import detect_kpi_alerts_for_store


class AnomalyAgent:
    def __init__(self, rules_path: str):
        self.rules_path = rules_path

    def run(self, kpis: Dict[str, Any]) -> List[Dict[str, Any]]:
        if "store_id" not in kpis:
            return []
        return detect_kpi_alerts_for_store(kpis, self.rules_path)
