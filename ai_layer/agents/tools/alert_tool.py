from __future__ import annotations
from typing import Dict, Any, List
import yaml
from data_platform.streaming.flink_jobs.alert_detection_job import detect_alerts


def load_rules(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def detect_kpi_alerts_for_store(kpis: Dict[str, Any], rules_path: str) -> List[Dict[str, Any]]:
    rules = load_rules(rules_path)
    store_id = str(kpis.get("store_id", "UNKNOWN"))
    return detect_alerts({store_id: kpis}, rules)
