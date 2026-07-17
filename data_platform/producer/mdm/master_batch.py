"""Scheduled batch producer for master data topics.

Runs the master data producers in periodic batches. Each batch emits a fixed
number of records per topic, then waits for the next schedule interval.

Usage
-----
python -m data_platform.producer.mdm.master_batch --batch-size 200 --interval-seconds 3600
python -m data_platform.producer.mdm.master_batch --batch-size 500 --runs 3
"""

from __future__ import annotations

import argparse
import logging
import os
import threading

from data_platform.producer.main import install_signal_handlers, run_aliases
from data_platform.producer.topics import PRODUCER_TYPES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("canonical.producer.master_batch")
EXPECTED_AIRFLOW_DAG_ID = "mdm_daily_processing"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m data_platform.producer.mdm.master_batch",
        description="Scheduled batch producer for master data topics",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=200,
        help="Number of messages per master topic for each batch run (default: 200)",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=3600.0,
        help="Seconds between batch runs (default: 3600)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        help="How many batch runs to execute (default: infinite)",
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
    return parser


def main() -> None:
    dag_id = os.environ.get("AIRFLOW_CTX_DAG_ID")
    if dag_id != EXPECTED_AIRFLOW_DAG_ID:
        raise RuntimeError(
            "master_batch is restricted to Airflow DAG execution only "
            f"(expected AIRFLOW_CTX_DAG_ID={EXPECTED_AIRFLOW_DAG_ID!r}, got {dag_id!r})"
        )

    args = build_parser().parse_args()
    aliases = list(PRODUCER_TYPES["master_data"])

    stop_event = threading.Event()
    install_signal_handlers(stop_event)

    run_index = 0
    while not stop_event.is_set() and (args.runs is None or run_index < args.runs):
        run_index += 1
        logger.info("Starting master batch run %d topics=%s", run_index, ",".join(aliases))
        run_aliases(
            aliases=aliases,
            brokers=args.brokers,
            schema_registry=args.schema_registry,
            count=args.batch_size,
            interval=0.0,
            stop_event=stop_event,
            install_signals=False,
        )

        if stop_event.is_set() or (args.runs is not None and run_index >= args.runs):
            break

        logger.info("Master batch run %d complete. Waiting %.2fs", run_index, args.interval_seconds)
        if stop_event.wait(args.interval_seconds):
            break

    logger.info("Master batch producer stopped after %d run(s)", run_index)


if __name__ == "__main__":
    main()
