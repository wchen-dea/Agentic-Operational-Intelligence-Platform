from typing import Any

from ai_system.config.settings import settings
from ai_system.tools.alert_tool import load_rules


def get_thresholds() -> dict[str, Any]:
    rules = load_rules(settings.alert_rules_path)
    return rules.get("thresholds", {})


def threshold_min(metric: str, default: float = 0.0) -> float:
    return get_thresholds().get(metric, {}).get("min", default)


def threshold_max(metric: str, default: float = float("inf")) -> float:
    return get_thresholds().get(metric, {}).get("max", default)
