from __future__ import annotations
from typing import Dict, Any
from ai_layer.agents.tools.fetch_kpi_tool import fetch_store_kpis


class KPIAgent:
    def run(self, store_id: str | None, region: str | None) -> Dict[str, Any]:
        return fetch_store_kpis(store_id=store_id, region=region)
