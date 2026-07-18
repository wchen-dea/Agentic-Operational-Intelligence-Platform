"""Module for table functions."""

from pyflink.table import DataTypes
from pyflink.table.udf import udtf


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING(),
        DataTypes.FLOAT(),
        DataTypes.FLOAT(),
        DataTypes.FLOAT(),
        DataTypes.STRING(),
    ]
)
def extract_vehicle_trims(vehicle_id, year_number, make_name, model_name, vehicle_class_code, trims):
    for trim in trims or []:
        for asm in trim.assemblies or [None]:
            asm_id = asm.assemblyIdentifier if asm else "NONE"
            kafka_key = vehicle_id + "|" + trim.trimIdentifier + "|" + asm_id
            yield (
                kafka_key,
                vehicle_id,
                year_number,
                make_name,
                model_name,
                vehicle_class_code,
                trim.trimIdentifier,
                asm_id,
                trim.vehicleTrimDescription,
                asm.frontTireCrossSectionNumber if asm else None,
                asm.frontTireAspectRatio if asm else None,
                asm.frontWheelDiameterNumber if asm else None,
                asm.vehicleAssemblyDescription if asm else None,
            )
