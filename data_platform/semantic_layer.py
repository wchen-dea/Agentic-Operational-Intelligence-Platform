"""Typed semantic KPI layer — wraps raw metric values with context for AI-ready consumption.

Every KPIRecord carries its own description, unit, direction, and threshold so that
agents and LLMs can reason about the value without needing external lookups.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_CATALOG_PATH = Path(__file__).resolve().parent.parent / "data_platform" / "kpi_catalog.yaml"


# ---------------------------------------------------------------------------
# KPI catalog loader
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_kpi_catalog(path: str | None = None) -> dict[str, dict[str, Any]]:
    """Load the KPI catalog YAML and index by metric name."""
    catalog_path = Path(path) if path else _CATALOG_PATH
    if not catalog_path.exists():
        logger.warning("KPI catalog not found at %s", catalog_path)
        return {}
    with catalog_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    entries = raw.get("kpis", []) if isinstance(raw, dict) else []
    return {entry["name"]: entry for entry in entries if "name" in entry}


def get_kpi_metadata(metric_name: str) -> dict[str, Any]:
    """Return catalog metadata for a single KPI, or empty dict if unknown."""
    return _load_kpi_catalog().get(metric_name, {})


# ---------------------------------------------------------------------------
# Data provenance
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DataProvenance:
    """Records the origin and quality context of a data point."""

    computed_at: float = field(default_factory=time.time)
    window_start: str | None = None
    window_end: str | None = None
    event_count: int | None = None
    source: str = "sample"  # "aurora_mysql" | "streaming" | "sample"
    data_quality_flags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "computed_at": self.computed_at,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "event_count": self.event_count,
            "source": self.source,
            "data_quality_flags": list(self.data_quality_flags),
        }


# ---------------------------------------------------------------------------
# KPIRecord — semantic wrapper around a single metric value
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KPIRecord:
    """A single KPI value enriched with catalog metadata and provenance."""

    name: str
    value: float
    unit: str = "unknown"
    direction: str = "higher_is_better"  # "higher_is_better" | "lower_is_better"
    threshold_min: float | None = None
    threshold_max: float | None = None
    description: str = ""
    domain: str = ""
    provenance: DataProvenance = field(default_factory=DataProvenance)

    @property
    def is_anomalous(self) -> bool:
        """True if the value breaches any threshold."""
        if self.threshold_min is not None and self.value < self.threshold_min:
            return True
        if self.threshold_max is not None and self.value > self.threshold_max:
            return True
        return False

    @property
    def trend_label(self) -> str:
        """Placeholder — requires historical data; returns 'unknown' for now."""
        return "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "direction": self.direction,
            "threshold_min": self.threshold_min,
            "threshold_max": self.threshold_max,
            "is_anomalous": self.is_anomalous,
            "description": self.description,
            "domain": self.domain,
            "provenance": self.provenance.to_dict(),
        }

    def to_llm_summary(self) -> str:
        """One-line summary optimized for LLM prompt injection."""
        status = "ANOMALOUS" if self.is_anomalous else "ok"
        return f"{self.name}={self.value} {self.unit} [{status}] — {self.description}"


# ---------------------------------------------------------------------------
# StoreKPISnapshot — a full store's worth of semantic KPI records
# ---------------------------------------------------------------------------

@dataclass
class StoreKPISnapshot:
    """All KPIs for a single store, enriched with catalog metadata and provenance."""

    store_id: str | None = None
    region: str | None = None
    records: list[KPIRecord] = field(default_factory=list)
    provenance: DataProvenance = field(default_factory=DataProvenance)

    @property
    def anomalous_records(self) -> list[KPIRecord]:
        return [r for r in self.records if r.is_anomalous]

    def to_flat_dict(self) -> dict[str, Any]:
        """Return the traditional flat dict for backward compatibility."""
        result: dict[str, Any] = {}
        if self.store_id:
            result["store_id"] = self.store_id
        if self.region:
            result["region"] = self.region
        for r in self.records:
            result[r.name] = r.value
        return result

    def to_llm_context(self) -> str:
        """Compact, self-describing text block for LLM prompts."""
        scope = self.store_id or self.region or "unknown"
        lines = [f"Store {scope} KPIs:"]
        for r in self.records:
            lines.append(f"  {r.to_llm_summary()}")
        anomalies = self.anomalous_records
        if anomalies:
            lines.append(f"Anomalies ({len(anomalies)}): " + ", ".join(r.name for r in anomalies))
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Factory: raw dict → StoreKPISnapshot
# ---------------------------------------------------------------------------

# Metrics that are identifiers, not KPI values
_NON_METRIC_KEYS = {"store_id", "region", "store_count", "stores"}


def enrich_kpis(
    raw: dict[str, Any],
    provenance: DataProvenance | None = None,
) -> StoreKPISnapshot:
    """Convert a flat KPI dict into a fully enriched StoreKPISnapshot.

    Looks up each metric name in the KPI catalog to attach unit, direction,
    description, and thresholds automatically.
    """
    prov = provenance or DataProvenance()
    records: list[KPIRecord] = []
    catalog = _load_kpi_catalog()

    for key, value in raw.items():
        if key in _NON_METRIC_KEYS:
            continue
        if not isinstance(value, (int, float)):
            continue
        meta = catalog.get(key, {})
        records.append(KPIRecord(
            name=key,
            value=float(value),
            unit=meta.get("unit", "unknown"),
            direction=meta.get("direction", "higher_is_better"),
            threshold_min=meta.get("threshold_min"),
            threshold_max=meta.get("threshold_max"),
            description=meta.get("description", ""),
            domain=meta.get("domain", ""),
            provenance=prov,
        ))

    return StoreKPISnapshot(
        store_id=raw.get("store_id"),
        region=raw.get("region"),
        records=records,
        provenance=prov,
    )
