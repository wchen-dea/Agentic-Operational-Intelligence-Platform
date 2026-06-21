"""Queryable KPI data adapter — abstracts the data source behind a clean interface.

In development, uses an in-process SQLite database seeded with sample data.
In production, swap to Aurora MySQL, Delta Lake, or any other backend by
implementing the ``KPIDataSource`` protocol.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Protocol

from data_platform.semantic_layer import DataProvenance, StoreKPISnapshot, enrich_kpis

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocol — implement this for any backend
# ---------------------------------------------------------------------------

class KPIDataSource(Protocol):
    """Interface that any KPI data backend must satisfy."""

    def fetch_by_store(self, store_id: str) -> dict[str, Any]: ...
    def fetch_by_region(self, region: str) -> dict[str, Any]: ...
    def fetch_all(self) -> list[dict[str, Any]]: ...
    def upsert(self, store_id: str, kpis: dict[str, Any]) -> None: ...


# ---------------------------------------------------------------------------
# SQLite implementation (dev / test)
# ---------------------------------------------------------------------------

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS store_kpis (
    store_id TEXT PRIMARY KEY,
    region TEXT,
    revenue_total REAL,
    order_count INTEGER,
    average_order_value REAL,
    appointment_show_rate REAL,
    appointment_to_order_conversion_rate REAL,
    invoice_total REAL,
    pos_invoice_capture_rate REAL,
    refund_rate REAL,
    inventory_in_stock_rate REAL,
    low_stock_sku_count INTEGER,
    stockout_sku_count INTEGER,
    inventory_turnover_proxy REAL,
    branded_revenue_mix_rate REAL,
    average_work_order_cycle_time_minutes REAL,
    overdue_work_order_count INTEGER,
    updated_at REAL
)
"""

# Seed data — same values as the previous SAMPLE_KPIS dict
_SEED_ROWS = [
    {
        "store_id": "245",
        "region": "Phoenix",
        "revenue_total": 820.0,
        "order_count": 9,
        "average_order_value": 91.1,
        "appointment_show_rate": 0.58,
        "appointment_to_order_conversion_rate": 0.21,
        "invoice_total": 790.0,
        "pos_invoice_capture_rate": 0.78,
        "refund_rate": 0.03,
        "inventory_in_stock_rate": 0.84,
        "low_stock_sku_count": 18,
        "stockout_sku_count": 6,
        "inventory_turnover_proxy": 0.13,
        "branded_revenue_mix_rate": 0.16,
        "average_work_order_cycle_time_minutes": 145.0,
        "overdue_work_order_count": 7,
    },
    {
        "store_id": "101",
        "region": "Phoenix",
        "revenue_total": 4300.0,
        "order_count": 41,
        "average_order_value": 104.9,
        "appointment_show_rate": 0.78,
        "appointment_to_order_conversion_rate": 0.39,
        "invoice_total": 4200.0,
        "pos_invoice_capture_rate": 0.94,
        "refund_rate": 0.02,
        "inventory_in_stock_rate": 0.95,
        "low_stock_sku_count": 5,
        "stockout_sku_count": 1,
        "inventory_turnover_proxy": 0.31,
        "branded_revenue_mix_rate": 0.29,
        "average_work_order_cycle_time_minutes": 82.0,
        "overdue_work_order_count": 1,
    },
]

_COLUMNS = [
    "store_id", "region", "revenue_total", "order_count", "average_order_value",
    "appointment_show_rate", "appointment_to_order_conversion_rate",
    "invoice_total", "pos_invoice_capture_rate", "refund_rate",
    "inventory_in_stock_rate", "low_stock_sku_count", "stockout_sku_count",
    "inventory_turnover_proxy", "branded_revenue_mix_rate",
    "average_work_order_cycle_time_minutes", "overdue_work_order_count",
    "updated_at",
]


class SQLiteKPISource:
    """SQLite-backed KPI data source for local development and testing."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    @contextmanager
    def _cursor(self):
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        finally:
            cur.close()

    def _init_db(self) -> None:
        with self._cursor() as cur:
            cur.execute(_CREATE_TABLE)
            cur.execute("SELECT COUNT(*) FROM store_kpis")
            if cur.fetchone()[0] == 0:
                self._seed(cur)

    def _seed(self, cur: sqlite3.Cursor) -> None:
        now = time.time()
        placeholders = ", ".join(["?"] * len(_COLUMNS))
        sql = f"INSERT OR REPLACE INTO store_kpis ({', '.join(_COLUMNS)}) VALUES ({placeholders})"
        for row in _SEED_ROWS:
            values = [row.get(c) for c in _COLUMNS[:-1]] + [now]
            cur.execute(sql, values)
        logger.info("Seeded %d sample KPI rows into SQLite", len(_SEED_ROWS))

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {k: row[k] for k in row.keys() if row[k] is not None}

    def fetch_by_store(self, store_id: str) -> dict[str, Any]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM store_kpis WHERE store_id = ?", (store_id,))
            row = cur.fetchone()
            if row is None:
                return {}
            return self._row_to_dict(row)

    def fetch_by_region(self, region: str) -> dict[str, Any]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM store_kpis WHERE region = ?", (region,))
            rows = cur.fetchall()
            if not rows:
                return {}

            dicts = [self._row_to_dict(r) for r in rows]
            n = len(dicts)
            # Aggregate: sums for absolutes, averages for rates
            _SUM_KEYS = {
                "revenue_total", "order_count", "invoice_total",
                "low_stock_sku_count", "stockout_sku_count",
                "overdue_work_order_count",
            }
            _AVG_KEYS = {
                "appointment_show_rate", "appointment_to_order_conversion_rate",
                "pos_invoice_capture_rate", "inventory_in_stock_rate",
                "branded_revenue_mix_rate", "average_work_order_cycle_time_minutes",
                "refund_rate", "inventory_turnover_proxy", "average_order_value",
            }
            result: dict[str, Any] = {"region": region, "store_count": n}
            for key in _SUM_KEYS:
                vals = [d[key] for d in dicts if key in d]
                if vals:
                    result[key] = sum(vals)
            for key in _AVG_KEYS:
                vals = [d[key] for d in dicts if key in d]
                if vals:
                    result[key] = sum(vals) / len(vals)
            return result

    def fetch_all(self) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM store_kpis")
            return [self._row_to_dict(r) for r in cur.fetchall()]

    def upsert(self, store_id: str, kpis: dict[str, Any]) -> None:
        kpis["store_id"] = store_id
        kpis["updated_at"] = time.time()
        placeholders = ", ".join(["?"] * len(_COLUMNS))
        sql = f"INSERT OR REPLACE INTO store_kpis ({', '.join(_COLUMNS)}) VALUES ({placeholders})"
        values = [kpis.get(c) for c in _COLUMNS]
        with self._cursor() as cur:
            cur.execute(sql, values)


# ---------------------------------------------------------------------------
# High-level fetch function (drop-in replacement for old fetch_store_kpis)
# ---------------------------------------------------------------------------

_default_source: KPIDataSource | None = None


def get_default_source() -> KPIDataSource:
    global _default_source
    if _default_source is None:
        _default_source = SQLiteKPISource()
    return _default_source


def fetch_store_kpis(
    store_id: str | None = None,
    region: str | None = None,
    source: KPIDataSource | None = None,
    enrich: bool = False,
) -> dict[str, Any] | StoreKPISnapshot:
    """Fetch KPIs from the configured data source.

    Args:
        store_id: Fetch KPIs for a specific store.
        region: Fetch aggregated KPIs for a region.
        source: Override the default data source.
        enrich: If True, return a StoreKPISnapshot with semantic metadata.

    Returns:
        Flat dict (backward-compatible) or StoreKPISnapshot if enrich=True.
    """
    src = source or get_default_source()
    provenance = DataProvenance(source="sqlite")

    if store_id:
        raw = src.fetch_by_store(store_id)
    elif region:
        raw = src.fetch_by_region(region)
    else:
        all_stores = src.fetch_all()
        if enrich:
            # Return first store enriched (or empty) for now
            raw = all_stores[0] if all_stores else {}
        else:
            return {"stores": all_stores}

    if enrich:
        return enrich_kpis(raw, provenance=provenance)
    return raw
