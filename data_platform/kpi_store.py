"""Queryable KPI data adapter - abstracts the data source behind a clean interface.

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
# Protocol - implement this for any backend
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

# Seed data - same values as the previous SAMPLE_KPIS dict
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
    "store_id",
    "region",
    "revenue_total",
    "order_count",
    "average_order_value",
    "appointment_show_rate",
    "appointment_to_order_conversion_rate",
    "invoice_total",
    "pos_invoice_capture_rate",
    "refund_rate",
    "inventory_in_stock_rate",
    "low_stock_sku_count",
    "stockout_sku_count",
    "inventory_turnover_proxy",
    "branded_revenue_mix_rate",
    "average_work_order_cycle_time_minutes",
    "overdue_work_order_count",
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
                "revenue_total",
                "order_count",
                "invoice_total",
                "low_stock_sku_count",
                "stockout_sku_count",
                "overdue_work_order_count",
            }
            _AVG_KEYS = {
                "appointment_show_rate",
                "appointment_to_order_conversion_rate",
                "pos_invoice_capture_rate",
                "inventory_in_stock_rate",
                "branded_revenue_mix_rate",
                "average_work_order_cycle_time_minutes",
                "refund_rate",
                "inventory_turnover_proxy",
                "average_order_value",
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
# Aurora MySQL / local Docker MySQL KPI source - queries PDM sink tables
# ---------------------------------------------------------------------------

# KPIs are computed from the PDM tables populated by the Kafka Connect JDBC
# Sink connectors (topic -> table, one-to-one name mapping).
# Tables referenced: sales_order, sales_order_receipt, sales_order_receipt_line_item,
#                    appointment, article, article_inventory, work_order
_PDM_KPI_SQL = """
WITH
-- ── Sales orders ─────────────────────────────────────────────────────────────
orders AS (
    SELECT
        site_number,
        COUNT(DISTINCT sales_order_identifier)  AS order_count
    FROM sales_order
    WHERE site_number = %%(site_id)s
      AND sales_order_created_date >= DATE_SUB(NOW(), INTERVAL %%(window_hours)s HOUR)
    GROUP BY site_number
),
-- ── Receipt revenue (actual billed amounts) ───────────────────────────────────
receipts AS (
    SELECT
        sor.site_number,
        SUM(sorli.net_price * sorli.sold_quantity)       AS revenue_total,
        COUNT(DISTINCT sor.sales_order_receipt_identifier) AS receipt_count,
        COUNT(DISTINCT sor.sales_order_identifier)        AS receipted_orders
    FROM sales_order_receipt sor
    JOIN sales_order_receipt_line_item sorli
        ON sor.sales_order_receipt_identifier = sorli.sales_order_receipt_identifier
    WHERE sor.site_number = %%(site_id)s
      AND sor.sales_order_receipt_posting_date >= DATE_SUB(NOW(), INTERVAL %%(window_hours)s HOUR)
    GROUP BY sor.site_number
),
-- ── Branded revenue (articles whose brand_category_code = 'B') ────────────────
branded AS (
    SELECT
        sor.site_number,
        SUM(sorli.net_price * sorli.sold_quantity) AS branded_revenue
    FROM sales_order_receipt sor
    JOIN sales_order_receipt_line_item sorli
        ON sor.sales_order_receipt_identifier = sorli.sales_order_receipt_identifier
    JOIN article a
        ON sorli.article_number = a.article_number
        AND a.brand_category_code = 'B'
    WHERE sor.site_number = %%(site_id)s
      AND sor.sales_order_receipt_posting_date >= DATE_SUB(NOW(), INTERVAL %%(window_hours)s HOUR)
    GROUP BY sor.site_number
),
-- ── Appointments ─────────────────────────────────────────────────────────────
appts AS (
    SELECT
        site_number,
        COUNT(DISTINCT appointment_identifier)                                      AS appt_total,
        SUM(CASE WHEN status_code IN ('showed','completed') THEN 1 ELSE 0 END)     AS appt_showed
    FROM appointment
    WHERE site_number = %%(site_id)s
    GROUP BY site_number
),
-- ── Inventory (latest snapshot date) ─────────────────────────────────────────
inventory AS (
    SELECT
        site_number,
        COUNT(*)                                                        AS sku_count,
        SUM(CASE WHEN available_quantity > 0 THEN 1 ELSE 0 END)        AS in_stock_count,
        SUM(CASE WHEN available_quantity = 0 THEN 1 ELSE 0 END)        AS stockout_count,
        SUM(CASE WHEN available_quantity > 0
                  AND available_quantity <= 2 THEN 1 ELSE 0 END)       AS low_stock_count
    FROM article_inventory
    WHERE site_number = %%(site_id)s
      AND inventory_date = (
            SELECT MAX(inventory_date) FROM article_inventory
            WHERE site_number = %%(site_id)s
      )
    GROUP BY site_number
),
-- ── Work orders ───────────────────────────────────────────────────────────────
work_orders AS (
    SELECT
        site_number,
        AVG(
            CASE WHEN bay_in_timestamp IS NOT NULL AND bay_out_timestamp IS NOT NULL
            THEN TIMESTAMPDIFF(MINUTE, bay_in_timestamp, bay_out_timestamp) END
        )                                                               AS avg_cycle_minutes,
        SUM(CASE WHEN delay_indicator = 1 THEN 1 ELSE 0 END)          AS delayed_count
    FROM work_order
    WHERE site_number = %%(site_id)s
      AND create_timestamp >= DATE_SUB(NOW(), INTERVAL %%(window_hours)s HOUR)
    GROUP BY site_number
)
SELECT
    %%(site_id)s                                                                    AS site_number,
    COALESCE(r.revenue_total,   0)                                                 AS revenue_total,
    COALESCE(o.order_count,     0)                                                 AS order_count,
    CASE WHEN COALESCE(o.order_count,0) > 0
         THEN r.revenue_total / o.order_count ELSE 0 END                           AS average_order_value,
    CASE WHEN COALESCE(a.appt_total,0) > 0
         THEN a.appt_showed / a.appt_total   ELSE 0 END                            AS appointment_show_rate,
    CASE WHEN COALESCE(a.appt_total,0) > 0
         THEN o.order_count / a.appt_total   ELSE 0 END                            AS appointment_to_order_conversion_rate,
    CASE WHEN COALESCE(o.order_count,0) > 0
         THEN r.receipt_count / o.order_count ELSE 0 END                           AS pos_invoice_capture_rate,
    COALESCE(r.revenue_total,   0)                                                 AS invoice_total,
    0.0                                                                            AS refund_rate,
    CASE WHEN COALESCE(i.sku_count,0) > 0
         THEN i.in_stock_count / i.sku_count  ELSE 0 END                           AS inventory_in_stock_rate,
    COALESCE(i.low_stock_count, 0)                                                 AS low_stock_sku_count,
    COALESCE(i.stockout_count,  0)                                                 AS stockout_sku_count,
    CASE WHEN COALESCE(i.sku_count,0) > 0
         THEN o.order_count / i.sku_count     ELSE 0 END                           AS inventory_turnover_proxy,
    CASE WHEN COALESCE(r.revenue_total,0) > 0
         THEN COALESCE(b.branded_revenue,0) / r.revenue_total ELSE 0 END           AS branded_revenue_mix_rate,
    COALESCE(w.avg_cycle_minutes, 0)                                               AS average_work_order_cycle_time_minutes,
    COALESCE(w.delayed_count,     0)                                               AS overdue_work_order_count
FROM       (SELECT %%(site_id)s AS site_number) base
LEFT JOIN  orders       o ON o.site_number = base.site_number
LEFT JOIN  receipts     r ON r.site_number = base.site_number
LEFT JOIN  branded      b ON b.site_number = base.site_number
LEFT JOIN  appts        a ON a.site_number = base.site_number
LEFT JOIN  inventory    i ON i.site_number = base.site_number
LEFT JOIN  work_orders  w ON w.site_number = base.site_number
"""


class AuroraMySQLKPISource:
    """Computes KPIs from the PDM MySQL sink tables populated by Kafka Connect.

    Works with both the local Docker MySQL (``mysql`` service in docker-compose)
    and Amazon Aurora MySQL in production.  Credentials are resolved in order:
      1. ``AURORA_PASSWORD`` environment variable (local / docker)
      2. AWS Secrets Manager secret at ``settings.aurora_mysql.password_secret_name``

    Args:
        window_hours: Rolling time window for sales/appointment/work-order aggregations.
    """

    def __init__(self, window_hours: int = 24) -> None:
        self._window = window_hours
        self._conn: Any = None
        self._connect()

    def _connect(self) -> None:
        try:
            import pymysql  # type: ignore[import]
            import json as _json
            import os as _os
        except ImportError as exc:
            raise ImportError("pymysql is required: uv add pymysql") from exc

        from ai_systems.config.settings import settings as s

        password = _os.environ.get("AURORA_PASSWORD")
        if not password:
            try:
                import boto3  # type: ignore[import]

                secret = boto3.client("secretsmanager").get_secret_value(SecretId=s.aurora_mysql.password_secret_name)
                password = _json.loads(secret["SecretString"]).get("password", "")
            except Exception as exc:
                raise RuntimeError(
                    f"Could not retrieve Aurora password from Secrets Manager "
                    f"({s.aurora_mysql.password_secret_name}): {exc}"
                ) from exc

        self._conn = pymysql.connect(
            host=s.aurora_mysql.host,
            port=s.aurora_mysql.port,
            db=s.aurora_mysql.database,
            user=s.aurora_mysql.username,
            password=password,
            charset="utf8mb4",
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
            ssl={"ca": _os.environ.get("AURORA_SSL_CA")} if _os.environ.get("AURORA_SSL_CA") else None,
        )
        logger.info("AuroraMySQLKPISource connected to %s", s.aurora_mysql.host)

    def _query(self, store_id: str) -> dict[str, Any]:
        import pymysql

        for attempt in range(2):
            try:
                with self._conn.cursor() as cur:
                    cur.execute(
                        _PDM_KPI_SQL,
                        {"site_id": store_id, "window_hours": self._window},
                    )
                    row = cur.fetchone()
                return dict(row) if row else {}
            except pymysql.OperationalError:
                if attempt == 0:
                    self._connect()  # reconnect once on stale connection
                else:
                    raise

    def fetch_by_store(self, store_id: str) -> dict[str, Any]:
        result = self._query(store_id)
        return result

    def fetch_by_region(self, region: str) -> dict[str, Any]:
        """Aggregate KPIs for all stores in a region.

        Looks up site numbers from the ``site`` PDM table (populated by the
        kronos.site Flink job), then aggregates per-store KPIs.
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT site_number FROM site WHERE region_code = %s LIMIT 50",
                    (region,),
                )
                rows = cur.fetchall()
        except Exception as exc:
            logger.error("AuroraMySQLKPISource.fetch_by_region failed: %s", exc)
            return {}

        if not rows:
            return {}
        store_kpis = [self.fetch_by_store(r["site_number"]) for r in rows]
        return _aggregate_region(store_kpis, region)

    def fetch_all(self) -> list[dict[str, Any]]:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT DISTINCT site_number FROM sales_order "
                    "WHERE sales_order_created_date >= DATE_SUB(NOW(), INTERVAL %s HOUR)",
                    (self._window,),
                )
                rows = cur.fetchall()
            return [self.fetch_by_store(r["site_number"]) for r in rows]
        except Exception as exc:
            logger.error("AuroraMySQLKPISource.fetch_all failed: %s", exc)
            return []

    def upsert(self, store_id: str, kpis: dict[str, Any]) -> None:
        raise NotImplementedError("Aurora source is read-only; write to source tables directly.")


# ---------------------------------------------------------------------------
# Delta Lake / Parquet gold-layer KPI source
# ---------------------------------------------------------------------------


class ParquetDeltaKPISource:
    """Reads pre-aggregated KPIs from Parquet files in the Delta Lake gold layer.

    The gold layer is written by the Flink/Databricks streaming job and read
    here using pandas + pyarrow (no Spark required for the API tier).

    ``base_path`` can be a local filesystem path, an S3 URI
    (``s3://bucket/path/``), or an ADLS path.  S3 access uses the default
    boto3 credential chain; install ``s3fs`` for transparent S3 reads.

    Args:
        base_path: Root directory of the gold layer KPI table.
        store_id_column: Column name for the store identifier.
    """

    def __init__(
        self,
        base_path: str,
        store_id_column: str = "store_id",
    ) -> None:
        self._base_path = base_path.rstrip("/")
        self._sid_col = store_id_column
        self._df: Any = None  # pandas DataFrame, lazy-loaded

    def _load(self) -> Any:
        if self._df is None:
            try:
                import pandas as pd  # type: ignore[import]
            except ImportError as exc:
                raise ImportError("pandas is required for ParquetDeltaKPISource: uv add pandas") from exc
            import glob

            pattern = f"{self._base_path}/**/*.parquet"
            files = glob.glob(pattern, recursive=True)
            if not files:
                logger.warning("No Parquet files found at %s", self._base_path)
                self._df = None
                return None
            self._df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
            logger.info("ParquetDeltaKPISource loaded %d rows from %s", len(self._df), self._base_path)
        return self._df

    def fetch_by_store(self, store_id: str) -> dict[str, Any]:
        df = self._load()
        if df is None:
            return {}
        rows = df[df[self._sid_col] == store_id]
        if rows.empty:
            return {}
        return rows.iloc[-1].to_dict()  # latest snapshot row

    def fetch_by_region(self, region: str) -> dict[str, Any]:
        df = self._load()
        if df is None:
            return {}
        if "region" not in df.columns:
            return {}
        rows = df[df["region"] == region]
        if rows.empty:
            return {}
        store_kpis = [rows[rows[self._sid_col] == sid].iloc[-1].to_dict() for sid in rows[self._sid_col].unique()]
        return _aggregate_region(store_kpis, region)

    def fetch_all(self) -> list[dict[str, Any]]:
        df = self._load()
        if df is None:
            return []
        return [df[df[self._sid_col] == sid].iloc[-1].to_dict() for sid in df[self._sid_col].unique()]

    def upsert(self, store_id: str, kpis: dict[str, Any]) -> None:
        raise NotImplementedError("Delta Lake source is read-only via this adapter.")


# ---------------------------------------------------------------------------
# Region aggregation helper
# ---------------------------------------------------------------------------

_SUM_KEYS = {
    "revenue_total",
    "order_count",
    "invoice_total",
    "low_stock_sku_count",
    "stockout_sku_count",
    "overdue_work_order_count",
}
_AVG_KEYS = {
    "appointment_show_rate",
    "appointment_to_order_conversion_rate",
    "pos_invoice_capture_rate",
    "inventory_in_stock_rate",
    "branded_revenue_mix_rate",
    "average_work_order_cycle_time_minutes",
    "refund_rate",
    "inventory_turnover_proxy",
    "average_order_value",
}


def _aggregate_region(store_kpis: list[dict[str, Any]], region: str) -> dict[str, Any]:
    n = len(store_kpis)
    result: dict[str, Any] = {"region": region, "store_count": n}
    for key in _SUM_KEYS:
        vals = [d[key] for d in store_kpis if key in d and d[key] is not None]
        if vals:
            result[key] = sum(vals)
    for key in _AVG_KEYS:
        vals = [d[key] for d in store_kpis if key in d and d[key] is not None]
        if vals:
            result[key] = sum(vals) / len(vals)
    return result


# ---------------------------------------------------------------------------
# KPI history store - persists snapshots for trend computation
# ---------------------------------------------------------------------------

_CREATE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS kpi_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id    TEXT    NOT NULL,
    metric_name TEXT    NOT NULL,
    value       REAL    NOT NULL,
    recorded_at REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_kpi_history_lookup
    ON kpi_history(store_id, metric_name, recorded_at);
"""


class KPIHistoryStore:
    """SQLite-backed store for KPI time-series history used by trend computation.

    In production, replace the SQLite backend with TimescaleDB, DynamoDB,
    or read directly from the Delta Lake silver/gold tables.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        import sqlite3 as _sqlite3

        self._conn = _sqlite3.connect(db_path, check_same_thread=False)
        for stmt in _CREATE_HISTORY_TABLE.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self._conn.execute(stmt)
        self._conn.commit()

    def record_snapshot(self, store_id: str, kpis: dict[str, Any]) -> None:
        """Persist a snapshot of all numeric KPI values for a store."""
        now = time.time()
        rows = [
            (store_id, k, float(v), now)
            for k, v in kpis.items()
            if isinstance(v, (int, float)) and k not in ("store_id", "region", "updated_at")
        ]
        if rows:
            self._conn.executemany(
                "INSERT INTO kpi_history (store_id, metric_name, value, recorded_at) VALUES (?,?,?,?)",
                rows,
            )
            self._conn.commit()

    def get_history(
        self,
        store_id: str,
        metric_name: str,
        days: int = 7,
    ) -> list[float]:
        """Return ordered historical values for a metric over the last N days."""
        cutoff = time.time() - days * 86400
        rows = self._conn.execute(
            "SELECT value FROM kpi_history "
            "WHERE store_id=? AND metric_name=? AND recorded_at>=? "
            "ORDER BY recorded_at ASC",
            (store_id, metric_name, cutoff),
        ).fetchall()
        return [r[0] for r in rows]


# ---------------------------------------------------------------------------
# High-level fetch function + source factory
# ---------------------------------------------------------------------------

_default_source: KPIDataSource | None = None
_history_store: KPIHistoryStore | None = None


def get_history_store() -> KPIHistoryStore:
    """Return the module-level KPI history store singleton."""
    global _history_store
    if _history_store is None:
        from ai_systems.config.settings import settings
        from pathlib import Path

        db_path = str(Path(settings.rag_corpus_path).parent.parent / ".data" / "kpi_history.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        _history_store = KPIHistoryStore(db_path=db_path)
    return _history_store


def build_kpi_source() -> KPIDataSource:
    """Factory: return the appropriate KPI source based on settings."""
    from ai_systems.config.settings import settings

    src = settings.kpi_source
    if src == "aurora_mysql":
        logger.info("Using AuroraMySQLKPISource")
        return AuroraMySQLKPISource()
    if src == "delta_lake":
        if not settings.delta_lake_gold_path:
            raise ValueError("AOIP_DELTA_LAKE_GOLD_PATH must be set when kpi_source=delta_lake")
        logger.info("Using ParquetDeltaKPISource at %s", settings.delta_lake_gold_path)
        return ParquetDeltaKPISource(base_path=settings.delta_lake_gold_path)
    logger.info("Using SQLiteKPISource (dev/test)")
    return SQLiteKPISource()


def get_default_source() -> KPIDataSource:
    global _default_source
    if _default_source is None:
        _default_source = build_kpi_source()
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
    from ai_systems.config.settings import settings

    src = source or get_default_source()
    source_label = settings.kpi_source if not source else "override"
    provenance = DataProvenance(source=source_label)

    if store_id:
        raw = src.fetch_by_store(store_id)
    elif region:
        raw = src.fetch_by_region(region)
    else:
        all_stores = src.fetch_all()
        if enrich:
            raw = all_stores[0] if all_stores else {}
        else:
            return {"stores": all_stores}

    # Record snapshot for trend history
    try:
        if store_id and raw:
            get_history_store().record_snapshot(store_id, raw)
    except Exception:
        pass  # history recording is best-effort

    if enrich:
        # Build history dict for trend computation
        history: dict[str, list[float]] = {}
        if store_id:
            from data_platform.semantic_layer import _load_kpi_catalog

            for metric_name in _load_kpi_catalog():
                vals = get_history_store().get_history(store_id, metric_name)
                if vals:
                    history[metric_name] = vals
        return enrich_kpis(raw, provenance=provenance, history=history or None)
    return raw
