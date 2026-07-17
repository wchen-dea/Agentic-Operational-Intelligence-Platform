"""Real-time producer for transaction data topics.

Runs transaction data producers continuously by default, using a configurable
message interval to mimic streaming traffic.

Usage
-----
python -m data_platform.producer.transaction.realtime --interval 0.2
python -m data_platform.producer.transaction.realtime --count 1000 --interval 0.1
"""

from __future__ import annotations

import argparse
import logging
import os
import time
import uuid
from collections import defaultdict
from typing import Any

from data_platform.producer.main import PRODUCERS, run_aliases
from data_platform.producer.topics import PRODUCER_TYPES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("canonical.producer.transaction_realtime")

MASTER_TOPIC_CONFIG: dict[str, dict[str, str]] = {
    "CanonicalWarehouseInventoryProduct": {"entity": "article", "id_field": "articleNumber"},
    "CanonicalSalesforceCrmCustomer": {"entity": "customer", "id_field": "customerIdentifier"},
    "CanonicalKronosEmployee": {"entity": "employee", "id_field": "employeeIdentifier"},
    "CanonicalKronosSite": {"entity": "site", "id_field": "siteNumber"},
    "CanonicalTrendwellVehivleMaster": {"entity": "vehicle", "id_field": "vehicleIdentifier"},
}

DIRECT_FK_FIELDS: dict[str, str] = {
    "siteNumber": "site",
    "customerIdentifier": "customer",
    "vehicleIdentifier": "vehicle",
    "articleNumber": "article",
    "employeeIdentifier": "employee",
    "employeeIdCreatedBy": "employee",
    "employeeIdProcessedBy": "employee",
    "createWorkerIdentifier": "employee",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m data_platform.producer.transaction.realtime",
        description="Real-time producer for transaction data topics",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Messages per transaction topic (default: infinite)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.2,
        help="Seconds to wait between each produced message (default: 0.2)",
    )
    parser.add_argument(
        "--brokers",
        default=os.environ.get("KAFKA_BROKERS", "localhost:9092"),
        help="Kafka bootstrap servers",
    )
    parser.add_argument(
        "--schema-registry",
        default=os.environ.get("SCHEMA_REGISTRY_URL", "http://localhost:8081"),
        metavar="URL",
        help="Confluent Schema Registry URL",
    )
    parser.add_argument(
        "--fk-check-samples",
        type=int,
        default=20,
        help="Sample records per transaction topic for foreign-key validation (default: 20)",
    )
    parser.add_argument(
        "--fk-check-idle-seconds",
        type=float,
        default=5.0,
        help="Idle wait while scanning canonical master topics for FK validation (default: 5.0)",
    )
    parser.add_argument(
        "--skip-fk-check",
        action="store_true",
        help="Skip canonical foreign-key validation preflight",
    )
    return parser


def _load_master_id_sets(brokers: str, schema_registry: str, idle_seconds: float) -> dict[str, set[str]]:
    try:
        from confluent_kafka import Consumer
        from confluent_kafka.schema_registry import SchemaRegistryClient
        from confluent_kafka.schema_registry.avro import AvroDeserializer
        from confluent_kafka.serialization import MessageField, SerializationContext
    except ImportError as exc:
        raise RuntimeError("confluent-kafka is required for FK validation preflight") from exc

    consumer = Consumer(
        {
            "bootstrap.servers": brokers,
            "group.id": f"tx-fk-check-{uuid.uuid4()}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    sr_client = SchemaRegistryClient({"url": schema_registry})
    avro_deser = AvroDeserializer(sr_client)  # type: ignore[call-arg]

    id_sets: dict[str, set[str]] = {cfg["entity"]: set() for cfg in MASTER_TOPIC_CONFIG.values()}
    topics = list(MASTER_TOPIC_CONFIG)
    consumer.subscribe(topics)

    last_msg_at = time.time()
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                if time.time() - last_msg_at >= idle_seconds:
                    break
                continue
            if msg.error():
                continue

            last_msg_at = time.time()
            topic = msg.topic()
            if topic is None:
                continue

            topic_cfg = MASTER_TOPIC_CONFIG.get(topic)
            if topic_cfg is None:
                continue

            value = avro_deser(msg.value(), SerializationContext(topic, MessageField.VALUE))
            if not isinstance(value, dict):
                continue

            raw_id = value.get(topic_cfg["id_field"])
            if raw_id is None:
                continue

            id_sets[topic_cfg["entity"]].add(str(raw_id))
    finally:
        consumer.close()

    return id_sets


def _iter_foreign_keys(record: dict[str, Any]) -> list[tuple[str, str, str]]:
    refs: list[tuple[str, str, str]] = []

    for field_name, entity in DIRECT_FK_FIELDS.items():
        value = record.get(field_name)
        if value is not None:
            refs.append((entity, str(value), field_name))

    line_items = record.get("lineItems")
    if isinstance(line_items, list):
        for idx, item in enumerate(line_items):
            if isinstance(item, dict) and item.get("articleNumber") is not None:
                refs.append(("article", str(item["articleNumber"]), f"lineItems[{idx}].articleNumber"))

    employees = record.get("employees")
    if isinstance(employees, list):
        for idx, item in enumerate(employees):
            if isinstance(item, dict) and item.get("employeeIdentifier") is not None:
                refs.append(("employee", str(item["employeeIdentifier"]), f"employees[{idx}].employeeIdentifier"))

    return refs


def _apply_master_ids_to_fake_pools(master_ids: dict[str, set[str]]) -> None:
    from data_platform.producer import fake

    fake.ARTICLE_NUMS = sorted(master_ids.get("article", set()))
    fake.CUSTOMER_IDS = sorted(master_ids.get("customer", set()))
    fake.VEHICLE_IDS = sorted(master_ids.get("vehicle", set()))
    fake.EMPLOYEE_IDS = sorted(master_ids.get("employee", set()))
    fake.STORE_IDS = sorted(master_ids.get("site", set()))
    fake.STORE_CODES = [f"STORE{s}" for s in fake.STORE_IDS]
    fake.SITE_TO_REGION = {s: fake.REGION_CODES[i % len(fake.REGION_CODES)] for i, s in enumerate(fake.STORE_IDS)}

    person_nums: list[str] = []
    for employee_id in fake.EMPLOYEE_IDS:
        if employee_id.startswith("EMP") and employee_id[3:].isdigit():
            person_nums.append(f"P{int(employee_id[3:]):06d}")
    if not person_nums:
        person_nums = fake.PERSON_NUMS
    fake.PERSON_NUMS = person_nums
    fake.EMPLOYEE_TO_PERSON_NUM = {
        employee_id: fake.PERSON_NUMS[i % len(fake.PERSON_NUMS)]
        for i, employee_id in enumerate(fake.EMPLOYEE_IDS)
    }
    fake.rebuild_customer_store_map()

    logger.info(
        "Bound transaction ID pools to canonical MDM IDs article=%d customer=%d vehicle=%d employee=%d site=%d",
        len(fake.ARTICLE_NUMS),
        len(fake.CUSTOMER_IDS),
        len(fake.VEHICLE_IDS),
        len(fake.EMPLOYEE_IDS),
        len(fake.STORE_IDS),
    )


def _validate_transaction_foreign_keys(
    aliases: list[str],
    master_ids: dict[str, set[str]],
    brokers: str,
    schema_registry: str,
    samples_per_topic: int,
) -> None:
    if samples_per_topic <= 0:
        raise ValueError("--fk-check-samples must be greater than 0")

    missing_master = sorted(entity for entity, values in master_ids.items() if not values)
    if missing_master:
        raise RuntimeError(
            "Cannot validate transaction foreign keys: canonical master topics are empty for "
            + ", ".join(missing_master)
            + ". Run MDM batch first."
        )

    employee_numeric_ids = {
        emp_id[3:]
        for emp_id in master_ids.get("employee", set())
        if emp_id.startswith("EMP") and emp_id[3:].isdigit()
    }

    violations: dict[str, list[str]] = defaultdict(list)

    for alias in aliases:
        producer_cls = PRODUCERS[alias]
        producer = producer_cls(brokers=brokers, schema_registry_url=schema_registry)
        for _ in range(samples_per_topic):
            record = producer.generate()
            for entity, fk_value, field_path in _iter_foreign_keys(record):
                if entity == "employee" and fk_value.isdigit():
                    exists = fk_value in employee_numeric_ids
                else:
                    exists = fk_value in master_ids.get(entity, set())
                if not exists:
                    violations[alias].append(f"{field_path}={fk_value}")
                    if len(violations[alias]) >= 10:
                        break

            site_number = record.get("siteNumber")
            customer_identifier = record.get("customerIdentifier")
            if site_number is not None and customer_identifier is not None:
                from data_platform.producer import fake

                assigned_store = fake.store_for_customer(str(customer_identifier))
                if assigned_store is not None and str(site_number) != assigned_store:
                    violations[alias].append(
                        f"customer-store-mismatch customerIdentifier={customer_identifier} siteNumber={site_number}"
                    )
                    if len(violations[alias]) >= 10:
                        break

            if len(violations[alias]) >= 10:
                break

    if violations:
        details = "; ".join(f"{alias}: {', '.join(values)}" for alias, values in sorted(violations.items()))
        raise RuntimeError(
            "Foreign-key validation failed. Transaction references not found in canonical masters. "
            + details
        )

    logger.info("Foreign-key validation passed for %d transaction topics", len(aliases))


def main() -> None:
    args = build_parser().parse_args()
    aliases = list(PRODUCER_TYPES["transaction_data"])

    logger.info("Loading canonical master IDs from MDM topics ...")
    master_ids = _load_master_id_sets(
        brokers=args.brokers,
        schema_registry=args.schema_registry,
        idle_seconds=args.fk_check_idle_seconds,
    )

    missing_master = sorted(entity for entity, values in master_ids.items() if not values)
    if missing_master:
        raise RuntimeError(
            "Cannot run transaction realtime producer: canonical master topics are empty for "
            + ", ".join(missing_master)
            + ". Run MDM batch first."
        )

    _apply_master_ids_to_fake_pools(master_ids)

    if not args.skip_fk_check:
        _validate_transaction_foreign_keys(
            aliases=aliases,
            master_ids=master_ids,
            brokers=args.brokers,
            schema_registry=args.schema_registry,
            samples_per_topic=args.fk_check_samples,
        )

    logger.info("Starting transaction real-time producer topics=%s", ",".join(aliases))

    run_aliases(
        aliases=aliases,
        brokers=args.brokers,
        schema_registry=args.schema_registry,
        count=args.count,
        interval=args.interval,
    )


if __name__ == "__main__":
    main()
