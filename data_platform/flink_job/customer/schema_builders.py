"""Module for schema builders."""

from pyflink.table import Schema, DataTypes
from flink_job.customer.data_types import get_contacts, get_alternate_identifiers, get_vehicles


def consumer_customer_canonical_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("customerIdentifier", DataTypes.STRING().not_null())
        .column("customerTypeCode", DataTypes.STRING())
        .column("fullName", DataTypes.STRING())
        .column("organizationName", DataTypes.STRING())
        .column("fleetAccountIdentifier", DataTypes.STRING())
        .column("arAccountNumber", DataTypes.STRING())
        .column("createTimestamp", DataTypes.STRING())
        .column("lastUpdateTimestamp", DataTypes.STRING())
        .column("timeOffset", DataTypes.STRING())
        .column("contacts", get_contacts())
        .column("alternateIdentifiers", get_alternate_identifiers())
        .column("vehicles", get_vehicles())
        .build()
    )


def producer_customer_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("customerIdentifier", DataTypes.STRING().not_null())
        .column("customerTypeCode", DataTypes.STRING())
        .column("fullName", DataTypes.STRING())
        .column("organizationName", DataTypes.STRING())
        .column("fleetAccountIdentifier", DataTypes.STRING())
        .column("arAccountNumber", DataTypes.STRING())
        .column("createTimestamp", DataTypes.STRING())
        .column("lastModifyTimestamp", DataTypes.STRING())
        .column("timeOffset", DataTypes.STRING())
        .build()
    )


def producer_customer_contact_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("customerContactIdentifier", DataTypes.STRING().not_null())
        .column("customerIdentifier", DataTypes.STRING().not_null())
        .column("title", DataTypes.STRING())
        .column("firstName", DataTypes.STRING())
        .column("lastName", DataTypes.STRING())
        .column("phoneNumber", DataTypes.STRING())
        .column("alternatePhoneNumber", DataTypes.STRING())
        .column("email", DataTypes.STRING())
        .column("primaryContactIndicator", DataTypes.BOOLEAN())
        .build()
    )


def producer_customer_alt_id_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("customerAlternateIdentifier", DataTypes.STRING().not_null())
        .column("customerIdentifier", DataTypes.STRING().not_null())
        .column("sourceSystemName", DataTypes.STRING().not_null())
        .build()
    )


def producer_customer_vehicle_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("customerVehicleIdentifier", DataTypes.STRING().not_null())
        .column("customerIdentifier", DataTypes.STRING().not_null())
        .column("vehicleIdentifier", DataTypes.STRING().not_null())
        .build()
    )
