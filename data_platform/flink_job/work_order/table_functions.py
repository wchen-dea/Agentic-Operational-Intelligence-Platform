"""Module for table functions."""

from pyflink.table import DataTypes
from pyflink.table.udf import udtf


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.DOUBLE(),
        DataTypes.DOUBLE(),
    ]
)
def extract_line_items(wo_id, line_items):
    for li in line_items or []:
        if li.lineItemNumber is None:
            continue
        kafka_key = wo_id + "|" + li.lineItemNumber
        yield (
            kafka_key,
            wo_id,
            li.lineItemNumber,
            li.articleNumber,
            li.articleTypeCode,
            li.articleQuantity,
            li.articleUnitPriceAmount,
        )


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.INT(),
    ]
)
def extract_bay_assignments(wo_id, bay_assignments):
    for ba in bay_assignments or []:
        if ba.bayNumber is None:
            continue
        kafka_key = wo_id + "|" + ba.bayNumber
        start = ba.bayStartTimestamp.replace("Z", "") if ba.bayStartTimestamp else None
        end = ba.bayEndTimestamp.replace("Z", "") if ba.bayEndTimestamp else None
        yield (kafka_key, wo_id, ba.bayNumber, start, end, ba.bayTotalTime)


@udtf(result_types=[DataTypes.STRING().not_null(), DataTypes.STRING().not_null(), DataTypes.STRING().not_null()])
def extract_employees(wo_id, employees):
    for emp in employees or []:
        if emp.employeeIdentifier is None:
            continue
        kafka_key = wo_id + "|" + emp.employeeIdentifier
        yield (kafka_key, wo_id, emp.employeeIdentifier)
