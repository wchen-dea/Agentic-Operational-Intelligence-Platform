from pyflink.table import Schema, DataTypes
from flink_job.appointment.data_types import get_slot_reservations


def consumer_appointment_canonical_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("appointmentIdentifier", DataTypes.STRING().not_null())
        .column("appointmentTypeName", DataTypes.STRING())
        .column("salesOrderIdentifier", DataTypes.STRING().not_null())
        .column("customerIdentifier", DataTypes.STRING())
        .column("scheduledStartTimestamp", DataTypes.STRING())
        .column("actualStartTimestamp", DataTypes.STRING())
        .column("statusCode", DataTypes.STRING())
        .column("bookingOriginCode", DataTypes.STRING())
        .column("orderTypeName", DataTypes.STRING())
        .column("siteNumber", DataTypes.STRING().not_null())
        .column("customerTypeName", DataTypes.STRING())
        .column("scheduledDuration", DataTypes.DOUBLE())
        .column("appointmentDate", DataTypes.STRING())
        .column("createTimestamp", DataTypes.STRING())
        .column("lastModifyTimestamp", DataTypes.STRING())
        .column("timeOffset", DataTypes.STRING())
        .column("slotReservations", get_slot_reservations())
        .build()
    )


def producer_appointment_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("appointmentIdentifier", DataTypes.STRING().not_null())
        .column("appointmentTypeName", DataTypes.STRING())
        .column("salesOrderIdentifier", DataTypes.STRING().not_null())
        .column("customerIdentifier", DataTypes.STRING())
        .column("scheduledStartTimestamp", DataTypes.STRING())
        .column("actualStartTimestamp", DataTypes.STRING())
        .column("statusCode", DataTypes.STRING())
        .column("bookingOriginCode", DataTypes.STRING())
        .column("orderTypeName", DataTypes.STRING())
        .column("siteNumber", DataTypes.STRING().not_null())
        .column("customerTypeName", DataTypes.STRING())
        .column("scheduledDuration", DataTypes.DOUBLE())
        .column("appointmentDate", DataTypes.STRING())
        .column("createTimestamp", DataTypes.STRING())
        .column("lastModifyTimestamp", DataTypes.STRING())
        .column("timeOffset", DataTypes.STRING())
        .build()
    )


def producer_slot_reservation_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("slotReservationIdentifier", DataTypes.STRING().not_null())
        .column("appointmentIdentifier", DataTypes.STRING().not_null())
        .column("slotReservationTypeCode", DataTypes.STRING())
        .build()
    )
