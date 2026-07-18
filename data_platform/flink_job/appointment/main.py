"""Module for main."""

import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.table.expressions import col

from config import add_jars, get_application_properties, get_property_map, execute
from flink_job.appointment.logging_util import log_message
from flink_job.appointment.schema_builders import (
    consumer_appointment_canonical_schema_builder,
    producer_appointment_schema_builder,
    producer_slot_reservation_schema_builder,
)
from flink_job.appointment.table_functions import extract_slot_reservations
from flink_job.appointment.tables import create_input_kafka_table, create_output_kafka_table

if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    add_jars(env)
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)

    props = get_application_properties()
    log_message(f"Using properties: {props}", logging.INFO)

    src_cfg = get_property_map(props, "appointment.canonical")
    appt_cfg = get_property_map(props, "appointment")
    slot_cfg = get_property_map(props, "appointment.slot.reservation")

    create_input_kafka_table(t_env, consumer_appointment_canonical_schema_builder(), src_cfg)
    create_output_kafka_table(t_env, producer_appointment_schema_builder(), appt_cfg)
    create_output_kafka_table(t_env, producer_slot_reservation_schema_builder(), slot_cfg)

    src = t_env.from_path(src_cfg["table.name"])
    log_message(src.get_schema(), logging.INFO)

    ode_appointment = src.select(
        col("appointmentIdentifier").alias("kafkaKey"),
        col("appointmentIdentifier"),
        col("appointmentTypeName"),
        col("salesOrderIdentifier"),
        col("customerIdentifier"),
        col("scheduledStartTimestamp").replace("Z", "").alias("scheduledStartTimestamp"),
        col("actualStartTimestamp").replace("Z", "").alias("actualStartTimestamp"),
        col("statusCode"),
        col("bookingOriginCode"),
        col("orderTypeName"),
        col("siteNumber"),
        col("customerTypeName"),
        col("scheduledDuration"),
        col("appointmentDate"),
        col("createTimestamp").replace("Z", "").alias("createTimestamp"),
        col("lastModifyTimestamp").replace("Z", "").alias("lastModifyTimestamp"),
        col("timeOffset"),
    )

    ode_slot_reservation = src.flat_map(
        extract_slot_reservations(col("appointmentIdentifier"), col("slotReservations"))
    ).alias("kafkaKey", "slotReservationIdentifier", "appointmentIdentifier", "slotReservationTypeCode")

    ss = t_env.create_statement_set()
    ss.add_insert(appt_cfg["table.name"], ode_appointment)
    ss.add_insert(slot_cfg["table.name"], ode_slot_reservation)
    ss.attach_as_datastream()

    execute(env, "Appointment: canonical -> appointment + slot_reservation")
