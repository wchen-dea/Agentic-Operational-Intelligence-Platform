"""Module for table functions."""

from pyflink.table import DataTypes
from pyflink.table.udf import udtf


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING(),
    ]
)
def extract_slot_reservations(appointment_identifier, slot_reservations):
    for sr in slot_reservations or []:
        kafka_key = appointment_identifier + "|" + sr.slotReservationIdentifier
        yield (kafka_key, sr.slotReservationIdentifier, appointment_identifier, sr.slotReservationTypeCode)
