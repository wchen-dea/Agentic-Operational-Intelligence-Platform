"""Module for alert tool."""

import logging
from functools import lru_cache
from typing import Any

import yaml

from ai_systems.alerting.engine import detect_alerts

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def load_rules(path: str) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                logger.error("Alert rules at %s is not a valid dict", path)
                return {"thresholds": {}}
            return data
    except FileNotFoundError:
        logger.error("Alert rules file not found: %s", path)
        return {"thresholds": {}}
    except yaml.YAMLError as e:
        logger.error("Invalid YAML in alert rules %s: %s", path, e)
        return {"thresholds": {}}


def detect_kpi_alerts_for_store(kpis: dict[str, Any], rules_path: str) -> list[dict[str, Any]]:
    rules = load_rules(rules_path)
    store_id = str(kpis.get("store_id", "UNKNOWN"))
    return detect_alerts({store_id: kpis}, rules)
