"""Projects gold KPI snapshots into Neo4j for graph-based analytics and traversal."""

from __future__ import annotations

import logging
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from neo4j import GraphDatabase

from ai_systems.config.settings import settings

logger = logging.getLogger(__name__)

SPARK_THRIFT_HOST = os.getenv("SPARK_THRIFT_HOST", "spark-thriftserver")
SPARK_THRIFT_PORT = int(os.getenv("SPARK_THRIFT_PORT", "10000"))
GOLD_SOURCE_TABLE = os.getenv("GOLD_SOURCE_TABLE", "iceberg.gold.gold_store_kpis")
GOLD_KPI_LIMIT = int(os.getenv("GOLD_KPI_LIMIT", "250000"))

GOLD_KPI_SQL_TEMPLATE = """
SELECT
    store_id,
    CAST(kpi_date AS STRING) AS kpi_date,
    revenue_total,
    order_count,
    avg_order_value,
    appointment_show_rate,
    appointment_conversion_rate,
    refund_rate,
    work_order_count,
    overdue_work_order_count,
    in_stock_rate,
    updated_at
FROM {source}
WHERE store_id IS NOT NULL
  AND kpi_date IS NOT NULL
ORDER BY kpi_date DESC
LIMIT {limit}
"""


def _spark_connection():
    from pyhive import hive

    return hive.Connection(
        host=SPARK_THRIFT_HOST,
        port=SPARK_THRIFT_PORT,
        auth="NONE",
    )


def _query_rows(sql: str) -> list[dict[str, Any]]:
    conn = _spark_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def _to_primitive(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        store_id = str(row["store_id"])
        kpi_date = str(row["kpi_date"])
        normalized.append(
            {
                "snapshot_id": f"{store_id}:{kpi_date}",
                "store_id": store_id,
                "kpi_date": kpi_date,
                "revenue_total": _to_primitive(row.get("revenue_total")),
                "order_count": _to_primitive(row.get("order_count")),
                "avg_order_value": _to_primitive(row.get("avg_order_value")),
                "appointment_show_rate": _to_primitive(row.get("appointment_show_rate")),
                "appointment_conversion_rate": _to_primitive(row.get("appointment_conversion_rate")),
                "refund_rate": _to_primitive(row.get("refund_rate")),
                "work_order_count": _to_primitive(row.get("work_order_count")),
                "overdue_work_order_count": _to_primitive(row.get("overdue_work_order_count")),
                "in_stock_rate": _to_primitive(row.get("in_stock_rate")),
                "updated_at": _to_primitive(row.get("updated_at")),
            }
        )
    return normalized


def _ensure_constraints(driver) -> None:
    queries = [
        "CREATE CONSTRAINT store_site_number IF NOT EXISTS FOR (s:Store) REQUIRE s.site_number IS UNIQUE",
        "CREATE CONSTRAINT store_kpi_snapshot_id IF NOT EXISTS FOR (k:StoreKPI) REQUIRE k.snapshot_id IS UNIQUE",
    ]
    with driver.session(database=settings.neo4j.database) as session:
        for query in queries:
            session.run(query).consume()


def _upsert_gold_kpis(driver, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return

    query = """
    UNWIND $rows AS row
    MERGE (s:Store {site_number: row.store_id})
    MERGE (k:StoreKPI {snapshot_id: row.snapshot_id})
    SET k.store_id = row.store_id,
        k.kpi_date = row.kpi_date,
        k.revenue_total = row.revenue_total,
        k.order_count = row.order_count,
        k.avg_order_value = row.avg_order_value,
        k.appointment_show_rate = row.appointment_show_rate,
        k.appointment_conversion_rate = row.appointment_conversion_rate,
        k.refund_rate = row.refund_rate,
        k.work_order_count = row.work_order_count,
        k.overdue_work_order_count = row.overdue_work_order_count,
        k.in_stock_rate = row.in_stock_rate,
        k.source_updated_at = row.updated_at,
        k.updated_at = datetime()
    MERGE (s)-[r:HAS_KPI_SNAPSHOT]->(k)
    SET r.kpi_date = row.kpi_date,
        r.updated_at = datetime()
    """

    with driver.session(database=settings.neo4j.database) as session:
        session.run(query, rows=rows).consume()


def sync_gold_kpis() -> int:
    sql = GOLD_KPI_SQL_TEMPLATE.format(source=GOLD_SOURCE_TABLE, limit=GOLD_KPI_LIMIT)
    rows = _normalize_rows(_query_rows(sql))

    neo4j_password = os.getenv(settings.neo4j.password_env_var, "neo4j")
    driver = GraphDatabase.driver(settings.neo4j.uri, auth=(settings.neo4j.username, neo4j_password))
    try:
        _ensure_constraints(driver)
        _upsert_gold_kpis(driver, rows)
    finally:
        driver.close()

    return len(rows)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    count = sync_gold_kpis()
    logger.info("Neo4j gold KPI transform complete: snapshots=%s source=%s", count, GOLD_SOURCE_TABLE)


if __name__ == "__main__":
    main()
