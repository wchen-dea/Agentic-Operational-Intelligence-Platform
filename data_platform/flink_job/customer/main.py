"""Module for main."""

import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.table.expressions import col

from config import add_jars, get_application_properties, get_property_map, execute
from flink_job.customer.logging_util import log_message
from flink_job.customer.schema_builders import (
    consumer_customer_canonical_schema_builder,
    producer_customer_schema_builder,
    producer_customer_contact_schema_builder,
    producer_customer_alt_id_schema_builder,
    producer_customer_vehicle_schema_builder,
)
from flink_job.customer.table_functions import (
    extract_contacts,
    extract_alternate_identifiers,
    extract_customer_vehicles,
)
from flink_job.customer.tables import create_input_kafka_table, create_output_kafka_table

if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    add_jars(env)
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)

    props = get_application_properties()
    log_message(f"Using properties: {props}", logging.INFO)

    src_cfg = get_property_map(props, "customer.canonical")
    cust_cfg = get_property_map(props, "customer")
    contact_cfg = get_property_map(props, "customer.contact")
    alt_id_cfg = get_property_map(props, "customer.alternate.identifier")
    vehicle_cfg = get_property_map(props, "customer.vehicle")

    create_input_kafka_table(t_env, consumer_customer_canonical_schema_builder(), src_cfg)
    create_output_kafka_table(t_env, producer_customer_schema_builder(), cust_cfg)
    create_output_kafka_table(t_env, producer_customer_contact_schema_builder(), contact_cfg)
    create_output_kafka_table(t_env, producer_customer_alt_id_schema_builder(), alt_id_cfg)
    create_output_kafka_table(t_env, producer_customer_vehicle_schema_builder(), vehicle_cfg)

    src = t_env.from_path(src_cfg["table.name"])
    log_message(src.get_schema(), logging.INFO)

    ode_customer = src.select(
        col("customerIdentifier").alias("kafkaKey"),
        col("customerIdentifier"),
        col("customerTypeCode"),
        col("fullName"),
        col("organizationName"),
        col("fleetAccountIdentifier"),
        col("arAccountNumber"),
        col("createTimestamp").replace("Z", "").alias("createTimestamp"),
        col("lastUpdateTimestamp").replace("Z", "").alias("lastModifyTimestamp"),
        col("timeOffset"),
    )

    ode_contact = src.flat_map(extract_contacts(col("customerIdentifier"), col("contacts"))).alias(
        "kafkaKey",
        "customerContactIdentifier",
        "customerIdentifier",
        "title",
        "firstName",
        "lastName",
        "phoneNumber",
        "alternatePhoneNumber",
        "email",
        "primaryContactIndicator",
    )

    ode_alt_id = src.flat_map(
        extract_alternate_identifiers(col("customerIdentifier"), col("alternateIdentifiers"))
    ).alias("kafkaKey", "customerAlternateIdentifier", "customerIdentifier", "sourceSystemName")

    ode_vehicle = src.flat_map(extract_customer_vehicles(col("customerIdentifier"), col("vehicles"))).alias(
        "kafkaKey", "customerVehicleIdentifier", "customerIdentifier", "vehicleIdentifier"
    )

    ss = t_env.create_statement_set()
    ss.add_insert(cust_cfg["table.name"], ode_customer)
    ss.add_insert(contact_cfg["table.name"], ode_contact)
    ss.add_insert(alt_id_cfg["table.name"], ode_alt_id)
    ss.add_insert(vehicle_cfg["table.name"], ode_vehicle)
    ss.attach_as_datastream()

    execute(env, "Customer: canonical -> customer + contact + alternate_identifier + vehicle")
