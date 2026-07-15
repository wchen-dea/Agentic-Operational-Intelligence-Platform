"""CLI entry point - produce synthetic Avro messages to Kafka canonical topics.

Each canonical topic has a dedicated producer that generates realistic fake
records conforming to the Avro schema in data_platform/canonical/*.avsc.

Usage
-----
# Produce 100 appointment messages (docker defaults):
  python -m data_platform.producer.main --topic appointment --count 100

# Produce to all topics simultaneously (live mode, 0.5 s between each burst):
  python -m data_platform.producer.main --all --interval 0.5

# Multiple specific topics, custom Kafka / Schema Registry:
  python -m data_platform.producer.main \\
      --topic sales_order work_order vehicle_inspection \\
      --count 50 \\
      --brokers kafka:29092 \\
      --schema-registry http://schema-registry:8081

# Infinite live mode for a single topic:
  python -m data_platform.producer.main --topic inventory --interval 1

Environment variables (lower precedence than CLI flags):
    KAFKA_BROKERS          Kafka bootstrap servers  (default: localhost:9092)
    SCHEMA_REGISTRY_URL    Schema Registry URL      (default: http://localhost:8081)
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import threading
import time
from typing import Type

from data_platform.producer.base import AvroKafkaProducer

# ── Import all topic producers ────────────────────────────────────────────────
from data_platform.producer.topics.appointment import AppointmentProducer
from data_platform.producer.topics.customer import CustomerProducer
from data_platform.producer.topics.sales_order import SalesOrderProducer
from data_platform.producer.topics.sales_order_receipt import SalesOrderReceiptProducer
from data_platform.producer.topics.sales_order_hybris import SalesOrderHybrisProducer
from data_platform.producer.topics.voucher import VoucherProducer
from data_platform.producer.topics.vehicle_inspection import VehicleInspectionProducer
from data_platform.producer.topics.vehicle import VehicleProducer
from data_platform.producer.topics.work_order import WorkOrderProducer
from data_platform.producer.topics.article import ArticleProducer
from data_platform.producer.topics.inventory import InventoryProducer
from data_platform.producer.topics.crewtime import CrewtimeProducer
from data_platform.producer.topics.employee import EmployeeProducer
from data_platform.producer.topics.kronos_hours import KronosHoursProducer
from data_platform.producer.topics.site import SiteProducer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("canonical.producer")

# ── Registry: alias -> producer class ─────────────────────────────────────────
PRODUCERS: dict[str, Type[AvroKafkaProducer]] = {
    "appointment": AppointmentProducer,
    "customer": CustomerProducer,
    "sales_order": SalesOrderProducer,
    "sales_order_receipt": SalesOrderReceiptProducer,
    "sales_order_hybris": SalesOrderHybrisProducer,
    "voucher": VoucherProducer,
    "vehicle_inspection": VehicleInspectionProducer,
    "vehicle": VehicleProducer,
    "work_order": WorkOrderProducer,
    "article": ArticleProducer,
    "inventory": InventoryProducer,
    "crewtime": CrewtimeProducer,
    "employee": EmployeeProducer,
    "kronos_hours": KronosHoursProducer,
    "site": SiteProducer,
}


# ── CLI ───────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m data_platform.producer.main",
        description="Canonical Kafka topic producers - synthetic Avro message generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    topic_group = p.add_mutually_exclusive_group(required=True)
    topic_group.add_argument(
        "--topic",
        nargs="+",
        choices=list(PRODUCERS),
        metavar="TOPIC",
        help="One or more topic aliases to produce to: " + ", ".join(PRODUCERS),
    )
    topic_group.add_argument(
        "--all",
        action="store_true",
        help="Produce to all 15 canonical topics simultaneously",
    )
    p.add_argument(
        "--count",
        type=int,
        default=None,
        help="Messages per topic (default: infinite)",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=0.0,
        help="Seconds to wait between each produced message (default: 0 = as fast as possible)",
    )
    p.add_argument(
        "--brokers",
        default=os.environ.get("KAFKA_BROKERS", "localhost:9092"),
        help="Kafka bootstrap servers",
    )
    p.add_argument(
        "--schema-registry",
        default=os.environ.get("SCHEMA_REGISTRY_URL", "http://localhost:8081"),
        metavar="URL",
        help="Confluent Schema Registry URL",
    )
    return p


def _run_producer(
    cls: Type[AvroKafkaProducer],
    brokers: str,
    sr_url: str,
    count: int | None,
    interval: float,
    stop_event: threading.Event,
) -> None:
    producer = cls(brokers=brokers, schema_registry_url=sr_url)
    i = 0
    try:
        while not stop_event.is_set() and (count is None or i < count):
            producer.produce_one()
            i += 1
            if interval:
                time.sleep(interval)
    except Exception as exc:
        logger.exception("[%s] producer error: %s", cls.TOPIC, exc)
    finally:
        producer._producer.flush(timeout=15)
        logger.info("[%s] stopped after %d messages", cls.TOPIC, i)


def main() -> None:
    args = build_parser().parse_args()
    aliases = list(PRODUCERS) if args.all else args.topic

    logger.info(
        "Starting %d producer(s)  count=%s  interval=%.2fs  brokers=%s",
        len(aliases),
        args.count or "inf",
        args.interval,
        args.brokers,
    )

    stop_event = threading.Event()

    def _handle_signal(sig: int, _frame: object) -> None:
        logger.info("Signal %d - stopping all producers ...", sig)
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    if len(aliases) == 1:
        # Single producer - run in main thread (simpler error propagation)
        cls = PRODUCERS[aliases[0]]
        _run_producer(cls, args.brokers, args.schema_registry, args.count, args.interval, stop_event)
    else:
        # Multiple producers - one thread each
        threads: list[threading.Thread] = []
        for alias in aliases:
            cls = PRODUCERS[alias]
            t = threading.Thread(
                target=_run_producer,
                args=(cls, args.brokers, args.schema_registry, args.count, args.interval, stop_event),
                name=f"prod-{alias}",
                daemon=True,
            )
            t.start()
            threads.append(t)
            logger.info("  started: %-30s -> %s", alias, cls.TOPIC)

        try:
            for t in threads:
                t.join()
        except KeyboardInterrupt:
            stop_event.set()
            for t in threads:
                t.join(timeout=10)

    logger.info("All producers finished.")


if __name__ == "__main__":
    main()
