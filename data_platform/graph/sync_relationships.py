"""Builds Neo4j relationships for article-store, employee-store, and customer-store links."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import pymysql
from neo4j import GraphDatabase

from ai_systems.config.settings import settings

logger = logging.getLogger(__name__)

ARTICLE_STORE_SQL = """
SELECT
    ai.article_number AS article_number,
    ai.site_number AS site_number,
    MAX(ai.inventory_date) AS last_seen,
    MAX(COALESCE(ai.on_hand_quantity, 0)) AS on_hand_quantity
FROM article_inventory ai
WHERE ai.article_number IS NOT NULL
  AND ai.article_number <> ''
  AND ai.site_number IS NOT NULL
  AND ai.site_number <> ''
GROUP BY ai.article_number, ai.site_number
"""

EMPLOYEE_STORE_SQL = """
SELECT
    rel.employee_identifier,
    rel.site_number,
    MAX(rel.last_seen) AS last_seen
FROM (
    SELECT
        e.employee_identifier,
        e.store_code AS site_number,
        COALESCE(e.db_update_timestamp, e.db_create_timestamp) AS last_seen
    FROM employee e
    WHERE e.employee_identifier IS NOT NULL
      AND e.employee_identifier <> ''
      AND e.store_code IS NOT NULL
      AND e.store_code <> ''

    UNION ALL

    SELECT
        we.employee_identifier,
        wo.site_number,
        COALESCE(wo.last_modify_timestamp, wo.create_timestamp, wo.db_update_timestamp) AS last_seen
    FROM work_order_employee we
    JOIN work_order wo
      ON wo.work_order_identifier = we.work_order_identifier
    WHERE we.employee_identifier IS NOT NULL
      AND we.employee_identifier <> ''
      AND wo.site_number IS NOT NULL
      AND wo.site_number <> ''
) rel
GROUP BY rel.employee_identifier, rel.site_number
"""

CUSTOMER_STORE_SQL = """
SELECT
    rel.customer_identifier,
    rel.site_number,
    MAX(rel.last_seen) AS last_seen
FROM (
    SELECT
        so.customer_identifier,
        so.site_number,
        COALESCE(so.sales_order_created_date, DATE(so.db_create_timestamp)) AS last_seen
    FROM sales_order so
    WHERE so.customer_identifier IS NOT NULL
      AND so.customer_identifier <> ''
      AND so.site_number IS NOT NULL
      AND so.site_number <> ''

    UNION ALL

    SELECT
        sor.customer_identifier,
        sor.site_number,
        COALESCE(sor.sales_order_receipt_posting_date, DATE(sor.db_create_timestamp)) AS last_seen
    FROM sales_order_receipt sor
    WHERE sor.customer_identifier IS NOT NULL
      AND sor.customer_identifier <> ''
      AND sor.site_number IS NOT NULL
      AND sor.site_number <> ''

    UNION ALL

    SELECT
        ap.customer_identifier,
        ap.site_number,
        COALESCE(ap.appointment_date, DATE(ap.create_timestamp)) AS last_seen
    FROM appointment ap
    WHERE ap.customer_identifier IS NOT NULL
      AND ap.customer_identifier <> ''
      AND ap.site_number IS NOT NULL
      AND ap.site_number <> ''

    UNION ALL

    SELECT
        wo.customer_identifier,
        wo.site_number,
        DATE(wo.create_timestamp) AS last_seen
    FROM work_order wo
    WHERE wo.customer_identifier IS NOT NULL
      AND wo.customer_identifier <> ''
      AND wo.site_number IS NOT NULL
      AND wo.site_number <> ''
) rel
GROUP BY rel.customer_identifier, rel.site_number
"""


@dataclass
class SyncSummary:
    article_store_edges: int = 0
    employee_store_edges: int = 0
    customer_store_edges: int = 0


def _mysql_connection() -> pymysql.connections.Connection:
    password = os.getenv("AURORA_PASSWORD", "connect_pass")
    return pymysql.connect(
        host=settings.aurora_mysql.host,
        port=settings.aurora_mysql.port,
        user=settings.aurora_mysql.username,
        password=password,
        database=settings.aurora_mysql.database,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=10,
        read_timeout=30,
        write_timeout=30,
        charset="utf8mb4",
    )


def _query_rows(conn: pymysql.connections.Connection, sql: str) -> list[dict[str, Any]]:
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return list(cursor.fetchall())


def _iso_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _normalize_article_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {
                "article_number": str(row["article_number"]),
                "site_number": str(row["site_number"]),
                "last_seen": _iso_date(row.get("last_seen")),
                "on_hand_quantity": int(row.get("on_hand_quantity") or 0),
            }
        )
    return normalized


def _normalize_employee_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {
                "employee_identifier": str(row["employee_identifier"]),
                "site_number": str(row["site_number"]),
                "last_seen": _iso_date(row.get("last_seen")),
            }
        )
    return normalized


def _normalize_customer_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {
                "customer_identifier": str(row["customer_identifier"]),
                "site_number": str(row["site_number"]),
                "last_seen": _iso_date(row.get("last_seen")),
            }
        )
    return normalized


def _ensure_constraints(driver) -> None:
    constraint_queries = [
        "CREATE CONSTRAINT store_site_number IF NOT EXISTS FOR (s:Store) REQUIRE s.site_number IS UNIQUE",
        "CREATE CONSTRAINT article_number IF NOT EXISTS FOR (a:Article) REQUIRE a.article_number IS UNIQUE",
        "CREATE CONSTRAINT employee_identifier IF NOT EXISTS FOR (e:Employee) REQUIRE e.employee_identifier IS UNIQUE",
        "CREATE CONSTRAINT customer_identifier IF NOT EXISTS FOR (c:Customer) REQUIRE c.customer_identifier IS UNIQUE",
    ]
    with driver.session(database=settings.neo4j.database) as session:
        for query in constraint_queries:
            session.run(query).consume()


def _upsert_article_store(driver, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    query = """
    UNWIND $rows AS row
    MERGE (a:Article {article_number: row.article_number})
    MERGE (s:Store {site_number: row.site_number})
    MERGE (a)-[r:AVAILABLE_AT]->(s)
    SET r.last_seen = row.last_seen,
        r.on_hand_quantity = row.on_hand_quantity,
        r.updated_at = datetime()
    """
    with driver.session(database=settings.neo4j.database) as session:
        session.run(query, rows=rows).consume()


def _upsert_employee_store(driver, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    query = """
    UNWIND $rows AS row
    MERGE (e:Employee {employee_identifier: row.employee_identifier})
    MERGE (s:Store {site_number: row.site_number})
    MERGE (e)-[r:WORKS_AT]->(s)
    SET r.last_seen = row.last_seen,
        r.updated_at = datetime()
    """
    with driver.session(database=settings.neo4j.database) as session:
        session.run(query, rows=rows).consume()


def _upsert_customer_store(driver, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    query = """
    UNWIND $rows AS row
    MERGE (c:Customer {customer_identifier: row.customer_identifier})
    MERGE (s:Store {site_number: row.site_number})
    MERGE (c)-[r:VISITS]->(s)
    SET r.last_seen = row.last_seen,
        r.updated_at = datetime()
    """
    with driver.session(database=settings.neo4j.database) as session:
        session.run(query, rows=rows).consume()


def sync_relationships() -> SyncSummary:
    neo4j_password = os.getenv(settings.neo4j.password_env_var, "neo4j")
    driver = GraphDatabase.driver(settings.neo4j.uri, auth=(settings.neo4j.username, neo4j_password))

    with _mysql_connection() as conn:
        article_rows = _normalize_article_rows(_query_rows(conn, ARTICLE_STORE_SQL))
        employee_rows = _normalize_employee_rows(_query_rows(conn, EMPLOYEE_STORE_SQL))
        customer_rows = _normalize_customer_rows(_query_rows(conn, CUSTOMER_STORE_SQL))

    _ensure_constraints(driver)
    _upsert_article_store(driver, article_rows)
    _upsert_employee_store(driver, employee_rows)
    _upsert_customer_store(driver, customer_rows)
    driver.close()

    return SyncSummary(
        article_store_edges=len(article_rows),
        employee_store_edges=len(employee_rows),
        customer_store_edges=len(customer_rows),
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    summary = sync_relationships()
    logger.info(
        "Neo4j relationship sync complete: article-store=%s employee-store=%s customer-store=%s",
        summary.article_store_edges,
        summary.employee_store_edges,
        summary.customer_store_edges,
    )


if __name__ == "__main__":
    main()
