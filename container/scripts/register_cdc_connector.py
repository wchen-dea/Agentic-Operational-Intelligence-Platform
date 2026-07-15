#!/usr/bin/env python3
"""Register the Debezium MySQL CDC source connector.

Architecture
------------
MySQL binlog (ROW format)  -->  Debezium MySQL connector  -->  Kafka

Topic naming
------------
Debezium emits to:   {topic.prefix}.{database}.{table}
                     e.g.  dbz.retail_ops.sales_order

RegexRouter renames: dbz\\.retail_ops\\.(.+)  -->  cdc_$1
                     e.g.  cdc_sales_order

One connector captures all 52 retail_ops tables.

Schema history
--------------
Debezium maintains a schema history topic (_dbz_schema_history) in Kafka.
This is an internal topic; do not delete it between restarts.

Environment variables
---------------------
    CONNECT_URL              Kafka Connect REST API (default: http://kafka-connect:8083)
    MYSQL_HOST               MySQL hostname         (default: mysql)
    MYSQL_PORT               MySQL port             (default: 3306)
    MYSQL_USER               Debezium MySQL user    (default: debezium)
    MYSQL_PASSWORD           Debezium user password (default: debezium_pass)
    MYSQL_DATABASE           Source database        (default: retail_ops)
    KAFKA_BOOTSTRAP_SERVERS  Kafka brokers          (default: broker1:29092,broker2:29092,broker3:29092)
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

CONNECT_URL = os.environ.get("CONNECT_URL", "http://kafka-connect:8083")
MYSQL_HOST = os.environ.get("MYSQL_HOST", "mysql")
MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
MYSQL_USER = os.environ.get("MYSQL_USER", "debezium")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "debezium_pass")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "retail_ops")
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "broker1:29092,broker2:29092,broker3:29092")

MAX_WAIT_SECONDS = 120
CONNECTOR_NAME = "debezium-mysql-retail-ops"
TOPIC_PREFIX = "dbz"

# All 52 PDM tables in retail_ops (fully qualified: database.table)
_CDC_TABLES: list[str] = [
    # Time dimensions
    f"{MYSQL_DATABASE}.year",
    f"{MYSQL_DATABASE}.quarter",
    f"{MYSQL_DATABASE}.month_of_year",
    f"{MYSQL_DATABASE}.month",
    f"{MYSQL_DATABASE}.week",
    f"{MYSQL_DATABASE}.day_of_the_week",
    f"{MYSQL_DATABASE}.date",
    f"{MYSQL_DATABASE}.hour",
    f"{MYSQL_DATABASE}.mtd",
    f"{MYSQL_DATABASE}.ytd",
    # Site / location / organisation reference
    f"{MYSQL_DATABASE}.region",
    f"{MYSQL_DATABASE}.site_blocking_reason",
    f"{MYSQL_DATABASE}.site_business_unit",
    f"{MYSQL_DATABASE}.site",
    f"{MYSQL_DATABASE}.agg_site_cutover_date",
    # Employee & product
    f"{MYSQL_DATABASE}.employee",
    f"{MYSQL_DATABASE}.article",
    f"{MYSQL_DATABASE}.article_inventory",
    f"{MYSQL_DATABASE}.vehicle",
    # Customer
    f"{MYSQL_DATABASE}.customer",
    f"{MYSQL_DATABASE}.customer_alternate_identifier",
    f"{MYSQL_DATABASE}.customer_contact",
    f"{MYSQL_DATABASE}.customer_vehicle",
    # Sales order header & children
    f"{MYSQL_DATABASE}.sales_order",
    f"{MYSQL_DATABASE}.sales_order_line_item",
    f"{MYSQL_DATABASE}.sales_order_line_item_fee",
    f"{MYSQL_DATABASE}.sales_order_line_item_promotion",
    f"{MYSQL_DATABASE}.sales_order_line_item_tax",
    f"{MYSQL_DATABASE}.sales_order_promotion",
    f"{MYSQL_DATABASE}.sales_order_treadwell_session",
    # Sales order receipt header & children
    f"{MYSQL_DATABASE}.sales_order_receipt",
    f"{MYSQL_DATABASE}.sales_order_receipt_line_item",
    f"{MYSQL_DATABASE}.sales_order_receipt_line_item_allocation",
    f"{MYSQL_DATABASE}.sales_order_receipt_line_item_fee",
    f"{MYSQL_DATABASE}.sales_order_receipt_line_item_promotion",
    f"{MYSQL_DATABASE}.sales_order_receipt_line_item_tax",
    f"{MYSQL_DATABASE}.sales_order_receipt_payment",
    f"{MYSQL_DATABASE}.sales_order_receipt_promotion",
    # Voucher
    f"{MYSQL_DATABASE}.voucher",
    # Appointment
    f"{MYSQL_DATABASE}.appointment",
    f"{MYSQL_DATABASE}.appointment_slot_reservation",
    # Work order & children
    f"{MYSQL_DATABASE}.work_order",
    f"{MYSQL_DATABASE}.work_order_bay_assignment",
    f"{MYSQL_DATABASE}.work_order_employee",
    f"{MYSQL_DATABASE}.work_order_line_item",
    # Vehicle inspection & detail
    f"{MYSQL_DATABASE}.vehicle_inspection",
    f"{MYSQL_DATABASE}.vehicle_tire_inspection_detail",
    f"{MYSQL_DATABASE}.vehicle_tire_inspection_measurement",
    # Labour / scheduling
    f"{MYSQL_DATABASE}.kronos_hours",
    f"{MYSQL_DATABASE}.reflexis_weekly_staff_metrics",
    # Security
    f"{MYSQL_DATABASE}.agg_store_security",
    f"{MYSQL_DATABASE}.store_security",
]


def _connector_config() -> dict:
    return {
        "connector.class": "io.debezium.connector.mysql.MySqlConnector",
        # MySQL connection
        "database.hostname": MYSQL_HOST,
        "database.port": MYSQL_PORT,
        "database.user": MYSQL_USER,
        "database.password": MYSQL_PASSWORD,
        "database.server.id": "184054",
        # Topic prefix — becomes first segment of Debezium's default topic name
        "topic.prefix": TOPIC_PREFIX,
        # Scope to the retail_ops database and specific tables only
        "database.include.list": MYSQL_DATABASE,
        "table.include.list": ",".join(_CDC_TABLES),
        # Internal schema history topic (Debezium creates it automatically)
        "schema.history.internal.kafka.bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "schema.history.internal.kafka.topic": "_dbz_schema_history",
        # Emit only data change events; skip DDL-only schema change events
        "include.schema.changes": "false",
        # Snapshot: capture current table state on first start, then switch to streaming
        "snapshot.mode": "initial",
        # Emit full row (before + after) for UPDATE events
        "tombstones.on.delete": "true",
        # Converters — JSON (no embedded schema) for simplicity;
        # switch to Avro per-table by overriding in future if needed
        "key.converter": "org.apache.kafka.connect.json.JsonConverter",
        "key.converter.schemas.enable": "false",
        "value.converter": "org.apache.kafka.connect.json.JsonConverter",
        "value.converter.schemas.enable": "false",
        # Rename topics: dbz.retail_ops.<table>  -->  cdc_<table>
        "transforms": "route",
        "transforms.route.type": "org.apache.kafka.connect.transforms.RegexRouter",
        "transforms.route.regex": f"{TOPIC_PREFIX}\\.{MYSQL_DATABASE}\\.(.+)",
        "transforms.route.replacement": "cdc_$1",
        # Error handling
        "errors.tolerance": "all",
        "errors.deadletterqueue.topic.name": "_dlq_connect_errors",
        "errors.deadletterqueue.topic.replication.factor": "1",
        "errors.log.enable": "true",
        "errors.log.include.messages": "true",
        # Tasks (single task — binlog is a single ordered stream)
        "tasks.max": "1",
    }


def _http(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    url = CONNECT_URL + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw) if raw.strip() else {}


def _wait_for_connect(max_wait: int = MAX_WAIT_SECONDS) -> None:
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{CONNECT_URL}/connectors", timeout=5) as r:
                if r.status == 200:
                    print(f"  Kafka Connect is ready at {CONNECT_URL}")
                    return
        except Exception:
            pass
        print(f"  Waiting for Kafka Connect at {CONNECT_URL} ...")
        time.sleep(5)
    raise RuntimeError(f"Kafka Connect did not become ready within {max_wait}s")


def main() -> None:
    print(f"=== Registering Debezium MySQL CDC connector: {CONNECTOR_NAME} ===")
    print(f"  MySQL source  : {MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
    print(f"  Tables        : {len(_CDC_TABLES)} tables")
    print(f"  Topic pattern : cdc_<table_name>")
    print()

    _wait_for_connect()

    # Check if connector already exists
    status, existing = _http("GET", f"/connectors/{CONNECTOR_NAME}/status")
    if status == 200:
        connector_state = existing.get("connector", {}).get("state", "UNKNOWN")
        print(f"  Connector already exists (state: {connector_state}) — skipping registration")
        print(f"  To force re-register, DELETE /connectors/{CONNECTOR_NAME} first")
        sys.exit(0)

    # Register the connector
    payload = {"name": CONNECTOR_NAME, "config": _connector_config()}
    status, resp = _http("POST", "/connectors", payload)

    if status in (200, 201):
        print(f"  OK  {CONNECTOR_NAME} registered successfully")
        print(f"      capturing {len(_CDC_TABLES)} tables -> cdc_* topics")
    elif status == 409:
        print(f"  SKIP  {CONNECTOR_NAME} already exists (HTTP 409)")
    else:
        print(f"  ERR  HTTP {status}: {json.dumps(resp, indent=2)}")
        sys.exit(1)

    # Show first few cdc_* topic names for confirmation
    print()
    print("  Sample topic mappings:")
    sample_tables = ["sales_order", "appointment", "work_order", "customer", "vehicle_inspection"]
    for t in sample_tables:
        print(f"    {MYSQL_DATABASE}.{t}  -->  cdc_{t}")
    print(f"    ... and {len(_CDC_TABLES) - len(sample_tables)} more")


if __name__ == "__main__":
    main()
