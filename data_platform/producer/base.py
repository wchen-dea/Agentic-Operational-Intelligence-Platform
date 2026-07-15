"""Base Avro Kafka producer for canonical topics.

Each topic producer subclass must implement ``generate() -> dict`` and
declare ``TOPIC`` (Kafka topic name) and ``SCHEMA_FILE`` (filename in
``data_platform/canonical/``).

Usage (direct):
    from data_platform.producer.base import AvroKafkaProducer

Environment variables (all overridable via CLI):
    KAFKA_BROKERS          bootstrap servers  (default: localhost:9092)
    SCHEMA_REGISTRY_URL    Schema Registry URL (default: http://localhost:8081)
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CANONICAL_DIR = Path(__file__).resolve().parents[1] / "schema"


class AvroKafkaProducer:
    """Abstract base - subclass and implement ``generate()``."""

    #: Kafka topic name, e.g. "salesforce.crm.appointment"
    TOPIC: str = ""
    #: Avro schema filename inside data_platform/canonical/
    SCHEMA_FILE: str = ""

    def __init__(
        self,
        brokers: str | None = None,
        schema_registry_url: str | None = None,
    ) -> None:
        self._brokers = brokers or os.environ.get("KAFKA_BROKERS", "localhost:9092")
        self._sr_url = schema_registry_url or os.environ.get("SCHEMA_REGISTRY_URL", "http://localhost:8081")
        self._schema_str = self._load_schema()
        self._producer = self._build_producer()
        self._produced = 0
        self._errors = 0

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _load_schema(self) -> str:
        path = _CANONICAL_DIR / self.SCHEMA_FILE
        if not path.exists():
            raise FileNotFoundError(f"Avro schema not found: {path}")
        return path.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Producer
    # ------------------------------------------------------------------

    def _build_producer(self) -> Any:
        try:
            from confluent_kafka import SerializingProducer  # type: ignore[import]
            from confluent_kafka.schema_registry import SchemaRegistryClient  # type: ignore[import]
            from confluent_kafka.schema_registry.avro import AvroSerializer  # type: ignore[import]
            from confluent_kafka.serialization import StringSerializer  # type: ignore[import]
        except ImportError as exc:
            raise ImportError("confluent-kafka is required: uv sync --group streaming") from exc

        sr_client = SchemaRegistryClient({"url": self._sr_url})
        avro_ser = AvroSerializer(sr_client, self._schema_str)
        string_ser = StringSerializer("utf_8")

        return SerializingProducer(
            {
                "bootstrap.servers": self._brokers,
                "key.serializer": string_ser,
                "value.serializer": avro_ser,
                "linger.ms": 5,
                "batch.size": 65536,
                "compression.type": "snappy",
            }
        )

    def _delivery_report(self, err: Any, msg: Any) -> None:
        if err:
            logger.warning("[%s] Delivery failed: %s", self.TOPIC, err)
            self._errors += 1
        else:
            self._produced += 1

    # ------------------------------------------------------------------
    # Override in subclass
    # ------------------------------------------------------------------

    def generate(self) -> dict[str, Any]:
        """Return a single record dict conforming to SCHEMA_FILE."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Produce API
    # ------------------------------------------------------------------

    def produce_one(self, record: dict[str, Any] | None = None) -> None:
        """Produce a single record (generate a new one if not supplied)."""
        if record is None:
            record = self.generate()
        kafka_key = record.get("kafkaKey") or ""
        self._producer.produce(
            topic=self.TOPIC,
            key=str(kafka_key),
            value=record,
            on_delivery=self._delivery_report,
        )
        self._producer.poll(0)

    def run(
        self,
        count: int | None = None,
        interval: float = 0.0,
        flush_every: int = 200,
    ) -> None:
        """Produce *count* records (or indefinitely if None) at *interval* seconds apart."""
        logger.info(
            "Producer started  topic=%s  brokers=%s  count=%s  interval=%.2fs",
            self.TOPIC,
            self._brokers,
            count or "inf",
            interval,
        )
        i = 0
        try:
            while count is None or i < count:
                self.produce_one()
                i += 1
                if i % flush_every == 0:
                    self._producer.flush(timeout=10)
                    logger.info("[%s] produced=%d  errors=%d", self.TOPIC, self._produced, self._errors)
                if interval:
                    time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("[%s] Interrupted after %d records.", self.TOPIC, i)
        finally:
            self._producer.flush(timeout=30)
            logger.info(
                "[%s] Done. produced=%d  errors=%d",
                self.TOPIC,
                self._produced,
                self._errors,
            )
