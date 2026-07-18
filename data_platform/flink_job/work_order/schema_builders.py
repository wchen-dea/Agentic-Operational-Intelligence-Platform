"""Module for schema builders."""

from pyflink.table import Schema, DataTypes
from flink_job.work_order.data_types import (
    get_line_items,
    get_bay_assignments,
    get_employees,
    get_contact,
)


def consumer_wom_canonical_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("workOrderIdentifier", DataTypes.STRING().not_null())
        .column("workOrderNumber", DataTypes.STRING().not_null())
        .column("orderTypeName", DataTypes.STRING())
        .column("salesOrderIdentifier", DataTypes.STRING())
        .column("appointmentIdentifier", DataTypes.STRING())
        .column("vehicleInspectionIdentifier", DataTypes.STRING())
        .column("siteNumber", DataTypes.STRING().not_null())
        .column("customerIdentifier", DataTypes.STRING())
        .column("vehicleIdentifier", DataTypes.STRING())
        .column("workOrderStatus", DataTypes.STRING())
        .column("workOrderCheckInTimestamp", DataTypes.STRING())
        .column("bayInTimestamp", DataTypes.STRING())
        .column("bayOutTimestamp", DataTypes.STRING())
        .column("promiseTime", DataTypes.STRING())
        .column("VIN", DataTypes.STRING())
        .column("totalArticleQuantity", DataTypes.DOUBLE())
        .column("delayIndicator", DataTypes.BOOLEAN())
        .column("delayReasonShort", DataTypes.STRING())
        .column("totalWaitTime", DataTypes.INT())
        .column("walkInIndicator", DataTypes.STRING())
        .column("delayReasonPrimary", DataTypes.STRING())
        .column("delayReasonSecondary", DataTypes.STRING())
        .column("delayReasonTertiary", DataTypes.STRING())
        .column("createTimestamp", DataTypes.STRING().not_null())
        .column("lastModifyTimestamp", DataTypes.STRING().not_null())
        .column("timeOffset", DataTypes.STRING())
        .column("workOrderType", DataTypes.STRING())
        .column("lineItems", get_line_items())
        .column("bayAssignments", get_bay_assignments())
        .column("employees", get_employees())
        .column("contact", get_contact())
        .build()
    )


def producer_work_order_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("workOrderIdentifier", DataTypes.STRING().not_null())
        .column("workOrderNumber", DataTypes.STRING().not_null())
        .column("orderTypeName", DataTypes.STRING())
        .column("salesOrderIdentifier", DataTypes.STRING())
        .column("appointmentIdentifier", DataTypes.STRING())
        .column("vehicleInspectionIdentifier", DataTypes.STRING())
        .column("siteNumber", DataTypes.STRING().not_null())
        .column("customerIdentifier", DataTypes.STRING())
        .column("vehicleIdentifier", DataTypes.STRING())
        .column("workOrderStatus", DataTypes.STRING())
        .column("workOrderCheckInTimestamp", DataTypes.STRING())
        .column("bayInTimestamp", DataTypes.STRING())
        .column("bayOutTimestamp", DataTypes.STRING())
        .column("vin", DataTypes.STRING())
        .column("delayIndicator", DataTypes.BOOLEAN())
        .column("delayReasonShort", DataTypes.STRING())
        .column("contactFirstName", DataTypes.STRING())
        .column("contactLastName", DataTypes.STRING())
        .column("contactEmail", DataTypes.STRING())
        .column("contactPhone", DataTypes.STRING())
        .column("createTimestamp", DataTypes.STRING().not_null())
        .column("lastModifyTimestamp", DataTypes.STRING().not_null())
        .column("timeOffset", DataTypes.STRING())
        .column("workOrderType", DataTypes.STRING())
        .build()
    )


def producer_wo_line_item_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("workOrderIdentifier", DataTypes.STRING().not_null())
        .column("lineItemNumber", DataTypes.STRING().not_null())
        .column("articleNumber", DataTypes.STRING())
        .column("articleTypeCode", DataTypes.STRING())
        .column("articleQuantity", DataTypes.DOUBLE())
        .column("articleUnitPriceAmount", DataTypes.DOUBLE())
        .build()
    )


def producer_wo_bay_assignment_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("workOrderIdentifier", DataTypes.STRING().not_null())
        .column("bayNumber", DataTypes.STRING().not_null())
        .column("bayStartTimestamp", DataTypes.STRING())
        .column("bayEndTimestamp", DataTypes.STRING())
        .column("bayTotalTime", DataTypes.INT())
        .build()
    )


def producer_wo_employee_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("workOrderIdentifier", DataTypes.STRING().not_null())
        .column("employeeIdentifier", DataTypes.STRING().not_null())
        .build()
    )
