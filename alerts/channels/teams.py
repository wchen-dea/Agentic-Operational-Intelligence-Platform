"""Microsoft Teams alert dispatch via Incoming Webhook.

Sends an Adaptive Card to the configured Teams channel when a KPI alert
fires.  Requires ``AOIP_TEAMS__WEBHOOK_URL`` (or ``settings.teams.webhook_url``)
to be set; if not set, the call is a no-op and a warning is logged so the
rest of the alert pipeline is unaffected.

Adaptive Card reference:
https://adaptivecards.io/explorer/
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

# Severity -> hex colour swatch shown on the card
_SEVERITY_COLOURS: dict[str, str] = {
    "critical": "FF0000",
    "high": "FF6600",
    "medium": "FFA500",
    "low": "FFCC00",
}


def _build_adaptive_card(alert: dict[str, Any]) -> dict[str, Any]:
    """Build a Teams Adaptive Card payload for a single KPI alert."""
    severity = str(alert.get("severity", "medium")).lower()
    colour = _SEVERITY_COLOURS.get(severity, settings.teams.accent_color)
    store_id = alert.get("store_id", "-")
    metric = alert.get("metric", "-")
    value = alert.get("value", "-")
    condition = alert.get("condition", "-")
    description = alert.get("description", "")
    remediation = alert.get("remediation", "")

    facts = [
        {"title": "Store", "value": str(store_id)},
        {"title": "Metric", "value": str(metric)},
        {"title": "Value", "value": str(value)},
        {"title": "Condition", "value": str(condition)},
        {"title": "Severity", "value": severity.upper()},
    ]
    if description:
        facts.append({"title": "Description", "value": description})
    if remediation:
        facts.append({"title": "Remediation", "value": remediation})

    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"🚨 Retail KPI Alert - Store {store_id}",
                            "weight": "Bolder",
                            "size": "Medium",
                            "color": "Attention" if severity in ("critical", "high") else "Warning",
                        },
                        {
                            "type": "FactSet",
                            "facts": facts,
                        },
                    ],
                    "msteams": {"width": "Full"},
                },
            }
        ],
    }


def format_teams_alert(alert: dict[str, Any]) -> str:
    """Return a plain-text summary of an alert (kept for logging and tests)."""
    return (
        f"Retail KPI Alert | Store {alert.get('store_id')} | "
        f"{alert.get('metric')}={alert.get('value')} | "
        f"Condition: {alert.get('condition')} | Severity: {alert.get('severity')}"
    )


def send_teams_alert(alert: dict[str, Any]) -> bool:
    """POST a KPI alert to the configured Teams Incoming Webhook.

    Returns ``True`` if the webhook accepted the message (HTTP 2xx),
    ``False`` otherwise.  Never raises - a failed webhook must not
    interrupt the alert dispatch pipeline.
    """
    webhook_url = settings.teams.webhook_url
    if not webhook_url:
        logger.warning(
            "Teams webhook not configured (AOIP_TEAMS__WEBHOOK_URL is unset). Alert suppressed: %s",
            format_teams_alert(alert),
        )
        return False

    payload = _build_adaptive_card(alert)

    try:
        with httpx.Client(timeout=settings.teams.timeout_seconds) as client:
            response = client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        if response.is_success:
            logger.info("Teams alert sent for store=%s metric=%s", alert.get("store_id"), alert.get("metric"))
            return True

        logger.error(
            "Teams webhook returned HTTP %s for store=%s metric=%s: %s",
            response.status_code,
            alert.get("store_id"),
            alert.get("metric"),
            response.text[:200],
        )
        return False

    except httpx.TimeoutException:
        logger.error(
            "Teams webhook timed out (%.1fs) for store=%s metric=%s",
            settings.teams.timeout_seconds,
            alert.get("store_id"),
            alert.get("metric"),
        )
        return False
    except Exception as exc:
        logger.exception(
            "Unexpected error sending Teams alert for store=%s: %s",
            alert.get("store_id"),
            exc,
        )
        return False


def send_teams_alerts(alerts: list[dict[str, Any]]) -> dict[str, int]:
    """Dispatch a batch of alerts to Teams.

    Returns a summary dict ``{"sent": N, "failed": M}``.
    """
    sent = 0
    failed = 0
    for alert in alerts:
        if send_teams_alert(alert):
            sent += 1
        else:
            failed += 1
    return {"sent": sent, "failed": failed}
