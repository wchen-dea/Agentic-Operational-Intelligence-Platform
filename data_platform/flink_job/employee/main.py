"""Module for main."""

import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.table.expressions import col

from config import add_jars, get_application_properties, get_property_map, execute
from flink_job.employee.logging_util import log_message
from flink_job.employee.schema_builders import (
    consumer_employee_canonical_schema_builder,
    producer_employee_schema_builder,
)
from flink_job.employee.tables import create_input_kafka_table, create_output_kafka_table

if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    add_jars(env)
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)
    props = get_application_properties()
    src_cfg = get_property_map(props, "employee.canonical")
    snk_cfg = get_property_map(props, "employee")
    create_input_kafka_table(t_env, consumer_employee_canonical_schema_builder(), src_cfg)
    create_output_kafka_table(t_env, producer_employee_schema_builder(), snk_cfg)
    src = t_env.from_path(src_cfg["table.name"])
    ode = src.select(
        col("employeeIdentifier").alias("kafkaKey"),
        col("employeeIdentifier"),
        col("fullName"),
        col("employeeTypeName"),
        col("storeCode"),
        col("employmentStatusCode"),
        col("effectiveStartDate").alias("positionEffectiveStartDate"),
        col("effectiveTerminationDate"),
        col("positionName"),
        col("positionJobCode"),
        col("originalHireDate"),
    )
    ss = t_env.create_statement_set()
    ss.add_insert(snk_cfg["table.name"], ode)
    ss.attach_as_datastream()
    execute(env, "Employee: canonical -> employee")
