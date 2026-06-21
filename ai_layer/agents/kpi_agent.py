from typing import Any

from ai_layer.agents.tools.fetch_kpi_tool import fetch_store_kpis


class KPIAgent:
    def run(self, store_id: str | None = None, region: str | None = None) -> dict[str, Any]:
        return fetch_store_kpis(store_id=store_id, region=region)
