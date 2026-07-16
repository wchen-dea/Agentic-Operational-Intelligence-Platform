import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.table.expressions import col

from config import add_jars, get_application_properties, get_property_map, execute
from flink_job.vehicle.logging_util import log_message
from flink_job.vehicle.schema_builders import (
    consumer_vehicle_canonical_schema_builder,
    producer_vehicle_schema_builder,
)
from flink_job.vehicle.table_functions import extract_vehicle_trims
from flink_job.vehicle.tables import create_input_kafka_table, create_output_kafka_table

if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    add_jars(env)
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)
    props = get_application_properties()
    src_cfg = get_property_map(props, "vehicle.canonical")
    snk_cfg = get_property_map(props, "vehicle")
    create_input_kafka_table(t_env, consumer_vehicle_canonical_schema_builder(), src_cfg)
    create_output_kafka_table(t_env, producer_vehicle_schema_builder(), snk_cfg)
    src = t_env.from_path(src_cfg["table.name"])
    ode = src.flat_map(
        extract_vehicle_trims(
            col("vehicleIdentifier"),
            col("yearNumber"),
            col("makeName"),
            col("modelName"),
            col("vehicleClassCode"),
            col("trims"),
        )
    ).alias(
        "kafkaKey",
        "vehicleIdentifier",
        "yearNumber",
        "makeName",
        "modelName",
        "vehicleClassCode",
        "trimIdentifier",
        "assemblyIdentifier",
        "vehicleTrimDescription",
        "frontTireCrossSectionNumber",
        "frontTireAspectRatio",
        "frontWheelDiameterNumber",
        "vehicleAssemblyDescription",
    )
    ss = t_env.create_statement_set()
    ss.add_insert(snk_cfg["table.name"], ode)
    ss.attach_as_datastream()
    execute(env, "Vehicle: canonical -> vehicle (one row per trim × assembly)")
