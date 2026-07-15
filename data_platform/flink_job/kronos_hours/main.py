import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.table.expressions import col

from config import add_jars, get_application_properties, get_property_map, execute
from data_platform.flink_jobs.kronos_hours.logging_util import log_message
from pyflink.table import DataTypes
from data_platform.flink_jobs.kronos_hours.schema_builders import (
    consumer_kronos_canonical_schema_builder,
    producer_kronos_hours_schema_builder,
)
from data_platform.flink_jobs.kronos_hours.tables import create_input_kafka_table, create_output_kafka_table

if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    add_jars(env)
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)
    props = get_application_properties()
    src_cfg = get_property_map(props, "kronos.canonical")
    snk_cfg = get_property_map(props, "CanonicalKronosHours")
    create_input_kafka_table(t_env, consumer_kronos_canonical_schema_builder(), src_cfg)
    create_output_kafka_table(t_env, producer_kronos_hours_schema_builder(), snk_cfg)
    src = t_env.from_path(src_cfg["table.name"])
    ode = src.select(
        (
            col("timeSheetItemIdentifier").cast(DataTypes.STRING()) + "|" + col("payCodeName") + "|" + col("startDTM")
        ).alias("kafkaKey"),
        col("personNumber"),
        col("adjustedApplyDate"),
        col("payCodeName"),
        col("payCodeType"),
        col("personFullName"),
        col("startDTM").replace("Z", "").alias("startTimestampLocal"),
        col("endDTM").replace("Z", "").alias("endTimestampLocal"),
        col("timeSheetItemIdentifier"),
        col("timeInSeconds"),
        col("timeOffset"),
    )
    ss = t_env.create_statement_set()
    ss.add_insert(snk_cfg["table.name"], ode)
    ss.attach_as_datastream()
    execute(env, "KronosHours: canonical -> kronos_hours")
