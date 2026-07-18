"""Module for schema builders."""

from pyflink.table import Schema, DataTypes


def consumer_kronos_canonical_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("personNumber", DataTypes.STRING().not_null())
        .column("personFullName", DataTypes.STRING())
        .column("payCodeName", DataTypes.STRING().not_null())
        .column("payCodeType", DataTypes.STRING().not_null())
        .column("timeInSeconds", DataTypes.STRING())
        .column("adjustedApplyDate", DataTypes.STRING())
        .column("startDTM", DataTypes.STRING().not_null())
        .column("endDTM", DataTypes.STRING())
        .column("timeSheetItemIdentifier", DataTypes.INT().not_null())
        .column("timeOffset", DataTypes.STRING())
        .build()
    )


def producer_kronos_hours_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("personNumber", DataTypes.STRING().not_null())
        .column("adjustedApplyDate", DataTypes.STRING())
        .column("payCodeName", DataTypes.STRING().not_null())
        .column("payCodeType", DataTypes.STRING().not_null())
        .column("personFullName", DataTypes.STRING())
        .column("startTimestampLocal", DataTypes.STRING().not_null())
        .column("endTimestampLocal", DataTypes.STRING())
        .column("timeSheetItemIdentifier", DataTypes.INT().not_null())
        .column("timeInSeconds", DataTypes.STRING())
        .column("timeOffset", DataTypes.STRING())
        .build()
    )
