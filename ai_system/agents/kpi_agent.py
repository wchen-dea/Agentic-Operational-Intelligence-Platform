from typing import Any

from data_platform.kpi_store import StoreKPISnapshot, fetch_store_kpis


class KPIAgent:
    def run(self, store_id: str | None = None, region: str | None = None) -> dict[str, Any] | StoreKPISnapshot:
        return fetch_store_kpis(store_id=store_id, region=region)
