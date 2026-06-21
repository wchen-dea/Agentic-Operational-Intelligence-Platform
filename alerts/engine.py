from typing import Any


def detect_alerts(kpis: dict[str, dict[str, Any]], rules: dict[str, Any]) -> list[dict[str, Any]]:
    alerts = []
    thresholds = rules.get("thresholds", {})
    for store_id, metrics in kpis.items():
        for metric, rule in thresholds.items():
            if metric not in metrics:
                continue
            value = metrics[metric]
            min_value = rule.get("min")
            max_value = rule.get("max")
            severity = rule.get("severity", "medium")

            if min_value is not None and value < min_value:
                alerts.append({
                    "store_id": store_id,
                    "metric": metric,
                    "value": value,
                    "condition": f"below_min_{min_value}",
                    "severity": severity,
                })
            if max_value is not None and value > max_value:
                alerts.append({
                    "store_id": store_id,
                    "metric": metric,
                    "value": value,
                    "condition": f"above_max_{max_value}",
                    "severity": severity,
                })
    return alerts
