import random, string
from pyflink.table import DataTypes
from pyflink.table.udf import udtf


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING(),
        DataTypes.BOOLEAN(),
        DataTypes.STRING(),
        DataTypes.DOUBLE(),
        DataTypes.STRING(),
    ]
)
def extract_details(inspection_identifier, tire_inspection_details):
    for d in tire_inspection_details or []:
        kafka_key = inspection_identifier + "|" + d.tirePositionCode
        yield (
            kafka_key,
            inspection_identifier,
            d.tirePositionCode,
            d.DOTNumber,
            d.recallIndicator,
            d.tireServicesPerformed,
            d.tireAge,
            d.tireStatus,
        )


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.FLOAT(),
    ]
)
def extract_measurements(inspection_identifier, tire_inspection_details):
    for d in tire_inspection_details or []:
        for m in d.tireInspectionMeasurements or []:
            loc = m.measurementLocation or "".join(random.choices(string.ascii_uppercase, k=5))
            kafka_key = inspection_identifier + "|" + d.tirePositionCode + "|" + loc
            try:
                val = float(m.measurementValue) if m.measurementValue else None
            except (ValueError, TypeError):
                val = None
            yield (kafka_key, inspection_identifier, d.tirePositionCode, loc, val)
