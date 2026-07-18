"""
Vector index pipeline — reads gold/analytics Iceberg tables, generates
embeddings, and upserts into Qdrant for AI semantic search.

Collections created
───────────────────
  store_kpi_narratives    — per-store KPI text narratives with metric payloads
  metric_definitions      — semantic model metric definitions for reasoning

Usage
─────
    python indexer.py                     # index all collections
    python indexer.py --collection store_kpi_narratives
    python indexer.py --dry-run           # print without upserting

Environment variables
─────────────────────
    QDRANT_HOST           (default: qdrant)
    QDRANT_PORT           (default: 6333)
    SPARK_THRIFT_HOST     (default: spark-thriftserver)
    SPARK_THRIFT_PORT     (default: 10000)
    EMBEDDING_MODEL       (default: sentence-transformers/all-MiniLM-L6-v2)
    KPI_SOURCE_TABLES     (default: warehouse.gold_store_kpis,iceberg.gold.gold_store_kpis)
    KPI_FALLBACK_MODE     (default: sample; use 'none' to disable fallback rows)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

logger = logging.getLogger("aoip.vector_indexer")

QDRANT_HOST = os.environ.get("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
THRIFT_HOST = os.environ.get("SPARK_THRIFT_HOST", "spark-thriftserver")
THRIFT_PORT = int(os.environ.get("SPARK_THRIFT_PORT", "10000"))
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
VECTOR_DIM = 384  # all-MiniLM-L6-v2 output dimension
KPI_SOURCE_TABLES = os.environ.get(
    "KPI_SOURCE_TABLES",
    "warehouse.gold_store_kpis,iceberg.gold.gold_store_kpis",
)
KPI_FALLBACK_MODE = os.environ.get("KPI_FALLBACK_MODE", "sample").strip().lower()

# Qdrant collection names
COLLECTION_KPI_NARRATIVES = "store_kpi_narratives"
COLLECTION_METRIC_DEFS = "metric_definitions"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_spark_conn():
    """Return a PyHive / PyArrow Spark Thrift connection."""
    try:
        from pyhive import hive

        conn = hive.Connection(
            host=THRIFT_HOST,
            port=THRIFT_PORT,
            auth="NONE",
        )
        return conn
    except ImportError as exc:
        logger.error("pyhive not installed: %s", exc)
        sys.exit(1)


def _query(conn, sql: str) -> list[dict]:
    cursor = conn.cursor()
    cursor.execute(sql)
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _candidate_kpi_sources() -> list[str]:
    """Return normalized table candidates for KPI source resolution.

    Supports either dot notation (`warehouse.gold_store_kpis`) or slash notation
    (`warehouse/gold_store_kpis`). Slash notation is normalized to dots.
    """
    candidates: list[str] = []
    for raw in KPI_SOURCE_TABLES.split(","):
        src = raw.strip()
        if not src:
            continue
        src = src.replace("/", ".")
        candidates.append(src)
    return candidates


def _short_error(exc: Exception, limit: int = 240) -> str:
    """Return a compact single-line exception string for logs."""
    text = str(exc).replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _sample_kpi_rows() -> list[dict]:
    """Return deterministic sample rows used when lakehouse sources are unavailable."""
    return [
        {
            "store_id": "245",
            "kpi_date": "2026-07-17",
            "order_count": 9,
            "revenue_total": 820.0,
            "avg_order_value": 91.1,
            "discount_total": 34.2,
            "appointment_count": 15,
            "appointment_show_count": 9,
            "appointment_show_rate_pct": 60.0,
            "appt_to_order_count": 4,
            "appt_conversion_rate_pct": 26.7,
            "invoice_total": 790.0,
            "net_revenue": 766.0,
            "refund_rate_pct": 3.0,
            "work_order_count": 12,
            "overdue_work_order_count": 3,
            "avg_work_order_cycle_time_minutes": 145.0,
            "sku_count": 221,
            "in_stock_rate_pct": 84.0,
            "total_inventory_value": 185000.0,
            "needs_reorder_count": 18,
        },
        {
            "store_id": "101",
            "kpi_date": "2026-07-17",
            "order_count": 41,
            "revenue_total": 4300.0,
            "avg_order_value": 104.9,
            "discount_total": 101.0,
            "appointment_count": 52,
            "appointment_show_count": 41,
            "appointment_show_rate_pct": 78.8,
            "appt_to_order_count": 20,
            "appt_conversion_rate_pct": 38.5,
            "invoice_total": 4200.0,
            "net_revenue": 4116.0,
            "refund_rate_pct": 2.0,
            "work_order_count": 35,
            "overdue_work_order_count": 1,
            "avg_work_order_cycle_time_minutes": 82.0,
            "sku_count": 310,
            "in_stock_rate_pct": 95.0,
            "total_inventory_value": 352000.0,
            "needs_reorder_count": 5,
        },
    ]


def _embedder():
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(EMBEDDING_MODEL)
    except ImportError as exc:
        logger.error("sentence-transformers not installed: %s", exc)
        sys.exit(1)


def _qdrant_client():
    try:
        from qdrant_client import QdrantClient

        return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    except ImportError as exc:
        logger.error("qdrant-client not installed: %s", exc)
        sys.exit(1)


def _ensure_collection(client, name: str, vector_size: int) -> None:
    from qdrant_client.models import Distance, VectorParams

    existing = {c.name for c in client.get_collections().collections}
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info("Created Qdrant collection: %s", name)


# ---------------------------------------------------------------------------
# Collection: store_kpi_narratives
# ---------------------------------------------------------------------------


def _build_kpi_narrative(row: dict) -> str:
    """Convert a gold KPI row into a human-readable narrative for embedding."""
    def _num(value, default=0):
        return default if value is None else value

    return (
        f"Store {row['store_id']} on {row['kpi_date']}: "
        f"revenue ${_num(row.get('revenue_total')):,.0f} "
        f"({_num(row.get('revenue_wow_growth')):+.1%} WoW), "
        f"order count {_num(row.get('order_count'))}, "
        f"avg order value ${_num(row.get('avg_order_value')):,.2f}, "
        f"appointment show rate {_num(row.get('appointment_show_rate_pct')):.1f}%, "
        f"appointment conversion {_num(row.get('appt_conversion_rate_pct')):.1f}%, "
        f"work orders {_num(row.get('work_order_count'))} "
        f"({_num(row.get('overdue_work_order_count'))} overdue), "
        f"avg cycle time {_num(row.get('avg_work_order_cycle_time_minutes')):.0f} min, "
        f"in-stock rate {_num(row.get('in_stock_rate_pct')):.1f}%, "
        f"inventory value ${_num(row.get('total_inventory_value')):,.0f}."
    )


def index_store_kpi_narratives(client, embedder, conn, dry_run: bool = False) -> int:
    # Ensure the collection exists even when source data is temporarily unavailable.
    _ensure_collection(client, COLLECTION_KPI_NARRATIVES, VECTOR_DIM)

    logger.info("Fetching gold KPI rows…")
    rows: list[dict] = []
    query_template = """
            SELECT
                store_id, kpi_date,
                order_count, revenue_total, avg_order_value, discount_total,
                appointment_count, appointment_show_count, appointment_show_rate_pct,
                appt_to_order_count, appt_conversion_rate_pct,
                invoice_total, net_revenue, refund_rate_pct,
                work_order_count, overdue_work_order_count, avg_work_order_cycle_time_minutes,
                sku_count, in_stock_rate_pct, total_inventory_value, needs_reorder_count
            FROM {source}
            ORDER BY kpi_date DESC
            LIMIT 10000
        """
    selected_source: str | None = None
    source_errors: list[str] = []
    for source in _candidate_kpi_sources():
        try:
            rows = _query(conn, query_template.format(source=source))
            selected_source = source
            logger.info("Using KPI source: %s", source)
            break
        except Exception as exc:
            source_errors.append(f"{source}: {_short_error(exc)}")

    if selected_source is None:
        if KPI_FALLBACK_MODE == "sample":
            rows = _sample_kpi_rows()
            selected_source = "fallback.sample"
            logger.warning(
                "KPI source table unavailable (%s); using fallback sample rows",
                " | ".join(source_errors) if source_errors else "no KPI sources configured",
            )
            logger.info("Using KPI source: %s", selected_source)
        else:
            logger.warning(
                "Skipping KPI narrative indexing: source table unavailable (%s)",
                " | ".join(source_errors) if source_errors else "no KPI sources configured",
            )
            return 0

    logger.info("  Fetched %d KPI rows", len(rows))

    if dry_run:
        for r in rows[:3]:
            print(_build_kpi_narrative(r))
        return len(rows)

    from qdrant_client.models import PointStruct

    batch_size = 128
    upserted = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        narratives = [_build_kpi_narrative(r) for r in batch]
        vectors = embedder.encode(narratives, show_progress_bar=False).tolist()
        points = [
            PointStruct(
                id=abs(hash(f"{r['store_id']}_{r['kpi_date']}")),
                vector=vec,
                payload={
                    "store_id": r["store_id"],
                    "kpi_date": str(r["kpi_date"]),
                    "narrative": narratives[j],
                    "revenue_total": r.get("revenue_total"),
                    "order_count": r.get("order_count"),
                    "show_rate_pct": r.get("appointment_show_rate_pct"),
                    "overdue_count": r.get("overdue_work_order_count"),
                    "in_stock_rate_pct": r.get("in_stock_rate_pct"),
                },
            )
            for j, (r, vec) in enumerate(zip(batch, vectors))
        ]
        client.upsert(collection_name=COLLECTION_KPI_NARRATIVES, points=points)
        upserted += len(points)
        logger.info(
            "  Upserted batch %d/%d (%d total)",
            i // batch_size + 1,
            (len(rows) + batch_size - 1) // batch_size,
            upserted,
        )

    return upserted


# ---------------------------------------------------------------------------
# Collection: metric_definitions
# ---------------------------------------------------------------------------

METRIC_DEFINITIONS: list[dict[str, str]] = [
    {"name": "revenue_total", "description": "Sum of all completed sales order revenue per store per day."},
    {"name": "average_order_value", "description": "Average revenue per completed sales order."},
    {
        "name": "appointment_show_rate",
        "description": "Percentage of scheduled appointments where the customer showed up.",
    },
    {
        "name": "appointment_conversion_rate",
        "description": "Percentage of showed appointments that converted to a sales order.",
    },
    {"name": "refund_rate", "description": "Percentage of invoiced revenue that was refunded."},
    {
        "name": "overdue_work_order_rate",
        "description": "Fraction of work orders that are past their due date and still open.",
    },
    {"name": "in_stock_rate", "description": "Percentage of SKUs that have at least one unit available."},
    {"name": "revenue_7d_cumulative", "description": "Rolling 7-day sum of daily revenue per store."},
    {"name": "revenue_28d_cumulative", "description": "Rolling 28-day sum of daily revenue per store."},
    {
        "name": "churn_risk_band",
        "description": "Customer churn risk classification: high (>90 days inactive), medium (>30 days), low (recently active).",
    },
    {
        "name": "reorder_pressure_rate",
        "description": "Fraction of SKUs that have fallen below their reorder threshold.",
    },
    {"name": "revenue_wow_growth", "description": "Week-over-week revenue growth rate: (today - 7d ago) / 7d ago."},
    {
        "name": "show_rate_delta_vs_7d",
        "description": "Today's appointment show rate minus the 7-day rolling average — signals emerging booking quality issues.",
    },
]


def index_metric_definitions(client, embedder, dry_run: bool = False) -> int:
    if dry_run:
        for m in METRIC_DEFINITIONS[:3]:
            print(f"{m['name']}: {m['description']}")
        return len(METRIC_DEFINITIONS)

    _ensure_collection(client, COLLECTION_METRIC_DEFS, VECTOR_DIM)

    from qdrant_client.models import PointStruct

    texts = [f"{m['name']}: {m['description']}" for m in METRIC_DEFINITIONS]
    vectors = embedder.encode(texts, show_progress_bar=False).tolist()
    points = [
        PointStruct(
            id=i,
            vector=vec,
            payload={"metric_name": m["name"], "description": m["description"]},
        )
        for i, (m, vec) in enumerate(zip(METRIC_DEFINITIONS, vectors))
    ]
    client.upsert(collection_name=COLLECTION_METRIC_DEFS, points=points)
    logger.info("Indexed %d metric definitions", len(points))
    return len(points)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    parser = argparse.ArgumentParser(description="Build Qdrant vector indexes")
    parser.add_argument(
        "--collection",
        choices=[COLLECTION_KPI_NARRATIVES, COLLECTION_METRIC_DEFS, "all"],
        default="all",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = _qdrant_client()
    embedder = _embedder()

    if args.collection in (COLLECTION_KPI_NARRATIVES, "all"):
        conn = _get_spark_conn()
        n = index_store_kpi_narratives(client, embedder, conn, dry_run=args.dry_run)
        logger.info("store_kpi_narratives: %d points indexed", n)
        conn.close()

    if args.collection in (COLLECTION_METRIC_DEFS, "all"):
        n = index_metric_definitions(client, embedder, dry_run=args.dry_run)
        logger.info("metric_definitions: %d points indexed", n)

    logger.info("Vector indexing complete.")


if __name__ == "__main__":
    main()
