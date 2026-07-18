"""Module for main."""

import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.table.expressions import col

from config import add_jars, get_application_properties, get_property_map, execute
from flink_job.crewtime.logging_util import log_message
from pyflink.table import DataTypes
from flink_job.crewtime.schema_builders import (
    consumer_crewtime_canonical_schema_builder,
    producer_reflexis_schema_builder,
)
from flink_job.crewtime.tables import create_input_kafka_table, create_output_kafka_table

if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    add_jars(env)
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)
    props = get_application_properties()
    src_cfg = get_property_map(props, "crewtime.canonical")
    snk_cfg = get_property_map(props, "reflexis.staff.metrics")
    create_input_kafka_table(t_env, consumer_crewtime_canonical_schema_builder(), src_cfg)
    create_output_kafka_table(t_env, producer_reflexis_schema_builder(), snk_cfg)
    src = t_env.from_path(src_cfg["table.name"])
    ode = src.select(
        (
            col("siteNumber")
            + "|"
            + col("systemStoreIdentifier").cast(DataTypes.STRING())
            + "|"
            + col("systemDepartmentIdentifier").cast(DataTypes.STRING())
            + "|"
            + col("staffGroup")
            + "|"
            + col("weekIndicator").cast(DataTypes.STRING())
            + "|"
            + col("systemDateIdentifier").cast(DataTypes.STRING())
        ).alias("kafkaKey"),
        col("siteNumber"),
        col("systemStoreIdentifier"),
        col("systemDepartmentIdentifier"),
        col("staffGroup"),
        col("weekIndicator"),
        col("systemDateIdentifier"),
        col("dateTimestamp").alias("createTimestamp"),
        col("lastModifyTimestamp"),
        col("demandHours"),
        col("systemGrossScheduledHours"),
        col("systemScheduledHours"),
        col("weekScheduledHours"),
        col("managerGrossScheduledHours"),
        col("managerScheduledHours"),
    )
    ss = t_env.create_statement_set()
    ss.add_insert(snk_cfg["table.name"], ode)
    ss.attach_as_datastream()
    execute(env, "Crewtime: canonical -> reflexis_weekly_staff_metrics")
