from pyflink.table import Schema, DataTypes
from flink_job.vehicle.data_types import get_trims


def consumer_vehicle_canonical_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("vehicleIdentifier", DataTypes.STRING().not_null())
        .column("yearNumber", DataTypes.STRING())
        .column("makeName", DataTypes.STRING())
        .column("modelName", DataTypes.STRING())
        .column("vehicleClassCode", DataTypes.STRING())
        .column("trims", get_trims())
        .build()
    )


def producer_vehicle_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("vehicleIdentifier", DataTypes.STRING().not_null())
        .column("yearNumber", DataTypes.STRING())
        .column("makeName", DataTypes.STRING())
        .column("modelName", DataTypes.STRING())
        .column("vehicleClassCode", DataTypes.STRING())
        .column("trimIdentifier", DataTypes.STRING().not_null())
        .column("assemblyIdentifier", DataTypes.STRING().not_null())
        .column("vehicleTrimDescription", DataTypes.STRING())
        .column("frontTireCrossSectionNumber", DataTypes.FLOAT())
        .column("frontTireAspectRatio", DataTypes.FLOAT())
        .column("frontWheelDiameterNumber", DataTypes.FLOAT())
        .column("vehicleAssemblyDescription", DataTypes.STRING())
        .build()
    )
