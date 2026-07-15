import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.table.expressions import col

from config import add_jars, get_application_properties, get_property_map, execute
from data_platform.flink_jobs.inventory.logging_util import log_message
from data_platform.flink_jobs.inventory.schema_builders import (
    consumer_inventory_canonical_schema_builder,
    producer_inventory_schema_builder,
)
from data_platform.flink_jobs.inventory.tables import create_input_kafka_table, create_output_kafka_table

if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    add_jars(env)
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)
    props = get_application_properties()
    src_cfg = get_property_map(props, "inventory.canonical")
    snk_cfg = get_property_map(props, "article.inventory")
    create_input_kafka_table(t_env, consumer_inventory_canonical_schema_builder(), src_cfg)
    create_output_kafka_table(t_env, producer_inventory_schema_builder(), snk_cfg)
    src = t_env.from_path(src_cfg["table.name"])
    ode = src.select(
        (col("siteNumber") + "|" + col("articleNumber")).alias("kafkaKey"),
        col("siteNumber"),
        col("articleNumber"),
        # Extract date from datetime string (YYYY-MM-DD)
        col("inventoryDateTime").substr(1, 10).alias("inventoryDate"),
        col("onHandQuantity"),
        col("reservedQuantity"),
        col("availableQuantity"),
        col("inTransitQuantity"),
        col("layawayQuantity"),
        col("weborderQuantity"),
        col("purchaseDecisionCode"),
        col("purchaseDecisionDescription"),
        col("timeOffset"),
    )
    ss = t_env.create_statement_set()
    ss.add_insert(snk_cfg["table.name"], ode)
    ss.attach_as_datastream()
    execute(env, "Inventory: canonical -> article_inventory")
