from __future__ import annotations
from typing import List, Dict, Any
from alerts.channels.teams import format_teams_alert


def dispatch_alerts(alerts: List[Dict[str, Any]]) -> List[str]:
    # Replace this with Teams webhook, ServiceNow, Jira, or PagerDuty integration.
    return [format_teams_alert(a) for a in alerts]
