from __future__ import annotations
from typing import Dict, Any


def format_teams_alert(alert: Dict[str, Any]) -> str:
    return (
        f"🚨 Retail KPI Alert | Store {alert.get('store_id')} | "
        f"{alert.get('metric')}={alert.get('value')} | "
        f"Condition: {alert.get('condition')} | Severity: {alert.get('severity')}"
    )
