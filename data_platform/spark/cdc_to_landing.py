"""Spark Structured Streaming — CDC topics → MinIO landing (Iceberg, append).

Reads Debezium JSON CDC events from Kafka, preserves the full CDC envelope
(before/after/op/ts_ms/source) and appends each event as a row to the
corresponding Iceberg table in the MinIO landing bucket.

Landing table naming:  iceberg.landing.<table_name>
  e.g. iceberg.landing.sales_orders

CDC Operation codes (Debezium):
  c  = CREATE  (new INSERT)
  u  = UPDATE
  d  = DELETE
  r  = READ    (initial snapshot)

Usage (inside spark-cdc-streaming container):
    spark-submit \
        --master spark://spark-master:7077 \
        cdc_to_landing.py [--topic <name>] [--all]

Environment variables:
    KAFKA_BROKERS          bootstrap servers  (default: broker1:29092,...)
    SCHEMA_REGISTRY_URL    Schema Registry    (default: http://schema-registry:8081)
    MINIO_ENDPOINT         MinIO S3 URL       (default: http://minio:9000)
    MINIO_ACCESS_KEY                          (default: minioadmin)
    MINIO_SECRET_KEY                          (default: minioadmin)
    ICEBERG_REST_URL       REST catalog URL   (default: http://iceberg-rest:8181)
    CHECKPOINT_BASE        checkpoint root    (default: s3a://checkpoints/cdc)
    SPARK_MASTER           master URL         (default: spark://spark-master:7077)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

logger = logging.getLogger("spark.cdc_to_landing")

# ---------------------------------------------------------------------------
# Topic → landing table mapping
# ---------------------------------------------------------------------------
CDC_TOPICS: dict[str, str] = {
    "cdc_appointment": "appointments",
    "cdc_appointment_slot_reservation": "appointment_slot_reservations",
    "cdc_article": "articles",
    "cdc_sales_order": "sales_orders",
    "cdc_article_inventory": "article_inventory",
    "cdc_customer": "customers",
    "cdc_customer_alternate_identifier": "customer_alternate_identifiers",
    "cdc_customer_contact": "customer_contacts",
    "cdc_customer_vehicle": "customer_vehicles",
    "cdc_employee": "employees",
    "cdc_kronos_hours": "kronos_hours",
    "cdc_reflexis_weekly_staff_metrics": "reflexis_weekly_staff_metrics",
    "cdc_sales_order_line_item": "sales_order_line_items",
    "cdc_sales_order_line_item_fee": "sales_order_line_item_fees",
    "cdc_sales_order_line_item_tax": "sales_order_line_item_taxes",
    "cdc_sales_order_promotion": "sales_order_promotions",
    "cdc_sales_order_receipt": "sales_order_receipts",
    "cdc_sales_order_receipt_line_item": "sales_order_receipt_line_items",
    "cdc_sales_order_receipt_line_item_fee": "sales_order_receipt_line_item_fees",
    "cdc_sales_order_receipt_line_item_tax": "sales_order_receipt_line_item_taxes",
    "cdc_sales_order_receipt_payment": "sales_order_receipt_payments",
    "cdc_site": "sites",
    "cdc_vehicle": "vehicles",
    "cdc_vehicle_inspection": "vehicle_inspections",
    "cdc_vehicle_tire_inspection_detail": "vehicle_tire_inspection_details",
    "cdc_vehicle_tire_inspection_measurement": "vehicle_tire_inspection_measurements",
    "cdc_voucher": "vouchers",
    "cdc_work_order": "work_orders",
    "cdc_work_order_bay_assignment": "work_order_bay_assignments",
    "cdc_work_order_employee": "work_order_employees",
    "cdc_work_order_line_item": "work_order_line_items",
}

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------
KAFKA_BROKERS = os.environ.get("KAFKA_BROKERS", "broker1:29092,broker2:29092,broker3:29092")
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
ICEBERG_REST_URL = os.environ.get("ICEBERG_REST_URL", "http://iceberg-rest:8181")
CHECKPOINT_BASE = os.environ.get("CHECKPOINT_BASE", "s3a://checkpoints/cdc")
SPARK_MASTER = os.environ.get("SPARK_MASTER", "spark://spark-master:7077")


def _build_spark_session():
    from pyspark.sql import SparkSession

    return (
        SparkSession.builder.master(SPARK_MASTER)
        .appName("cdc-to-landing")
        # ── Iceberg extensions ────────────────────────────────────────────
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        # ── Iceberg REST catalog ──────────────────────────────────────────
        .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.iceberg.type", "rest")
        .config("spark.sql.catalog.iceberg.uri", ICEBERG_REST_URL)
        .config("spark.sql.catalog.iceberg.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
        .config("spark.sql.catalog.iceberg.s3.endpoint", MINIO_ENDPOINT)
        .config("spark.sql.catalog.iceberg.s3.path-style-access", "true")
        .config("spark.sql.catalog.iceberg.s3.access-key-id", MINIO_ACCESS_KEY)
        .config("spark.sql.catalog.iceberg.s3.secret-access-key", MINIO_SECRET_KEY)
        .config("spark.sql.catalog.iceberg.warehouse", "s3://landing/")
        # ── S3A (Hadoop MinIO) ────────────────────────────────────────────
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
        .getOrCreate()
    )


# ---------------------------------------------------------------------------
# Debezium CDC JSON schema (outer envelope only — inner payload is dynamic)
# ---------------------------------------------------------------------------
_DEBEZIUM_SCHEMA = """
{
  "type": "struct",
  "fields": [
    {"field": "before",  "type": "string", "optional": true},
    {"field": "after",   "type": "string", "optional": true},
    {"field": "source",  "type": "string", "optional": true},
    {"field": "op",      "type": "string", "optional": false},
    {"field": "ts_ms",   "type": "long",   "optional": true},
    {"field": "transaction", "type": "string", "optional": true}
  ]
}
"""


def _stream_topic(spark, topic: str, table_name: str) -> None:
    """Start a streaming query for a single CDC topic → Iceberg landing table."""
    from pyspark.sql import functions as F
    from pyspark.sql.types import LongType

    # Create the Iceberg namespace + table if they don't exist
    spark.sql("CREATE NAMESPACE IF NOT EXISTS iceberg.landing")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS iceberg.landing.{table_name} (
            kafka_topic      STRING,
            kafka_partition  INT,
            kafka_offset     BIGINT,
            kafka_timestamp  TIMESTAMP,
            cdc_op           STRING  COMMENT 'c=create u=update d=delete r=read',
            cdc_ts_ms        BIGINT  COMMENT 'Debezium source timestamp (ms)',
            before_json      STRING  COMMENT 'Row state before the event (JSON)',
            after_json       STRING  COMMENT 'Row state after the event (JSON)',
            source_json      STRING  COMMENT 'Debezium source metadata (JSON)',
            ingested_at      TIMESTAMP
        )
        USING iceberg
        PARTITIONED BY (days(ingested_at))
        TBLPROPERTIES (
            'write.format.default' = 'parquet',
            'write.metadata.compression-codec' = 'gzip'
        )
    """)

    checkpoint_location = f"{CHECKPOINT_BASE}/{table_name}"

    # Ensure checkpoint directories exist before starting the stream.
    # This avoids transient FileNotFound errors when recovering after cleanup
    # or after object-store path churn.
    jvm = spark._jvm
    hadoop_conf = spark._jsc.hadoopConfiguration()
    fs = jvm.org.apache.hadoop.fs.Path(checkpoint_location).getFileSystem(hadoop_conf)
    for suffix in ("", "/offsets", "/commits", "/sources"):
        fs.mkdirs(jvm.org.apache.hadoop.fs.Path(f"{checkpoint_location}{suffix}"))

    # Read from Kafka
    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BROKERS)
        .option("kafka.client.dns.lookup", "use_all_dns_ips")
        .option("kafka.request.timeout.ms", "60000")
        .option("kafka.default.api.timeout.ms", "60000")
        .option("kafka.retry.backoff.ms", "500")
        .option("kafka.reconnect.backoff.ms", "500")
        .option("kafka.reconnect.backoff.max.ms", "10000")
        .option("kafka.metadata.max.age.ms", "30000")
        .option("subscribe", topic)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    # Parse the Debezium envelope (value is a JSON string)
    parsed = (
        raw.select(
            F.col("topic").alias("kafka_topic"),
            F.col("partition").alias("kafka_partition"),
            F.col("offset").alias("kafka_offset"),
            F.col("timestamp").alias("kafka_timestamp"),
            F.get_json_object(F.col("value").cast("string"), "$.op").alias("cdc_op"),
            F.get_json_object(F.col("value").cast("string"), "$.ts_ms").cast(LongType()).alias("cdc_ts_ms"),
            F.get_json_object(F.col("value").cast("string"), "$.before").alias("before_json"),
            F.get_json_object(F.col("value").cast("string"), "$.after").alias("after_json"),
            F.get_json_object(F.col("value").cast("string"), "$.source").alias("source_json"),
            F.current_timestamp().alias("ingested_at"),
        )
        # Filter out tombstone messages (null value = Kafka compaction tombstone)
        .filter(F.col("cdc_op").isNotNull())
    )

    # Write to Iceberg landing table (append — full CDC history preserved)
    query = (
        parsed.writeStream.format("iceberg")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_location)
        .toTable(f"iceberg.landing.{table_name}")
    )

    logger.info("Streaming query started: %s → iceberg.landing.%s", topic, table_name)
    return query


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    parser = argparse.ArgumentParser(description="CDC Kafka → MinIO/Iceberg landing")
    parser.add_argument("--topic", help="Single CDC topic name (key in CDC_TOPICS map)")
    parser.add_argument("--all", action="store_true", help="Stream all CDC topics (default)")
    args = parser.parse_args()

    if args.topic and args.topic not in CDC_TOPICS:
        print(f"ERROR: unknown topic '{args.topic}'. Available: {list(CDC_TOPICS)}", file=sys.stderr)
        sys.exit(1)

    topics_to_run: dict[str, str] = {args.topic: CDC_TOPICS[args.topic]} if args.topic else CDC_TOPICS

    spark = _build_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    # Some container images may preload Spark defaults that override catalog
    # settings at startup. Re-apply catalog conf before first Iceberg access.
    spark.conf.set("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    spark.conf.set("spark.sql.catalog.iceberg.type", "rest")
    spark.conf.set("spark.sql.catalog.iceberg.uri", ICEBERG_REST_URL)
    spark.conf.set("spark.sql.catalog.iceberg.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
    spark.conf.set("spark.sql.catalog.iceberg.s3.endpoint", MINIO_ENDPOINT)
    spark.conf.set("spark.sql.catalog.iceberg.s3.path-style-access", "true")
    spark.conf.set("spark.sql.catalog.iceberg.s3.access-key-id", MINIO_ACCESS_KEY)
    spark.conf.set("spark.sql.catalog.iceberg.s3.secret-access-key", MINIO_SECRET_KEY)
    spark.conf.set("spark.sql.catalog.iceberg.warehouse", "s3://landing/")
    spark.conf.set("spark.sql.defaultCatalog", "iceberg")

    logger.info(
        "Effective Iceberg catalog config: type=%s uri=%s warehouse=%s endpoint=%s",
        spark.conf.get("spark.sql.catalog.iceberg.type", "<missing>"),
        spark.conf.get("spark.sql.catalog.iceberg.uri", "<missing>"),
        spark.conf.get("spark.sql.catalog.iceberg.warehouse", "<missing>"),
        spark.conf.get("spark.sql.catalog.iceberg.s3.endpoint", "<missing>"),
    )
    logger.info("Effective Spark default catalog: %s", spark.conf.get("spark.sql.defaultCatalog", "<missing>"))

    queries = []
    for topic, table_name in topics_to_run.items():
        logger.info("Starting stream: %s → landing.%s", topic, table_name)
        q = _stream_topic(spark, topic, table_name)
        queries.append(q)

    # Block until all queries terminate (or Ctrl-C)
    try:
        for q in queries:
            q.awaitTermination()
    except KeyboardInterrupt:
        logger.info("Interrupted — stopping all streaming queries")
        for q in queries:
            q.stop()
        spark.stop()


if __name__ == "__main__":
    main()
