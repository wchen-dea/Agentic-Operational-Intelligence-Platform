import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.table.expressions import col

from config import add_jars, get_application_properties, get_property_map, execute
from flink_job.vehicle_inspection.logging_util import log_message
from flink_job.vehicle_inspection.schema_builders import (
    consumer_vtv_canonical_schema_builder,
    producer_inspection_schema_builder,
    producer_detail_schema_builder,
    producer_measurement_schema_builder,
)
from flink_job.vehicle_inspection.table_functions import extract_details, extract_measurements
from flink_job.vehicle_inspection.tables import create_input_kafka_table, create_output_kafka_table

if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    add_jars(env)
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)
    props = get_application_properties()
    src_cfg = get_property_map(props, "vtv.canonical")
    ins_cfg = get_property_map(props, "vehicle.inspection")
    det_cfg = get_property_map(props, "vehicle.detail")
    mea_cfg = get_property_map(props, "vehicle.measurement")
    create_input_kafka_table(t_env, consumer_vtv_canonical_schema_builder(), src_cfg)
    create_output_kafka_table(t_env, producer_inspection_schema_builder(), ins_cfg)
    create_output_kafka_table(t_env, producer_detail_schema_builder(), det_cfg)
    create_output_kafka_table(t_env, producer_measurement_schema_builder(), mea_cfg)
    src = t_env.from_path(src_cfg["table.name"])
    ode_ins = src.select(
        col("inspectionIdentifier").alias("kafkaKey"),
        col("inspectionIdentifier"),
        col("customerIdentifier"),
        col("DOTCommunicationOptInIndicator").alias("dotCommunicationOptInIndicator"),
        col("VIN").alias("vin"),
        col("vehicleLicensePlateNumber"),
        col("inspectionLocation"),
        col("storeCode"),
        col("siteNumber"),
        col("createWorkerIdentifier"),
        col("createBySourceName"),
        col("createTimestamp").replace("Z", "").alias("createTimestamp"),
        col("lastUpdateTimestamp").replace("Z", "").alias("lastModifyTimestamp"),
        col("mileageReading"),
        col("rotationPattern"),
        col("TPMSStatus").alias("tpmsStatus"),
        col("vehicleIdentifier"),
        col("originalReasonCode"),
        col("vehicleYear"),
        col("vehicleMake"),
        col("vehicleModel"),
        col("timeOffset"),
    )
    ode_det = src.flat_map(extract_details(col("inspectionIdentifier"), col("tireInspectionDetails"))).alias(
        "kafkaKey",
        "inspectionIdentifier",
        "tirePositionCode",
        "dotNumber",
        "recallIndicator",
        "tireServicesPerformed",
        "tireAge",
        "tireStatus",
    )
    ode_mea = src.flat_map(extract_measurements(col("inspectionIdentifier"), col("tireInspectionDetails"))).alias(
        "kafkaKey", "inspectionIdentifier", "tirePositionCode", "measurementLocation", "measurementValue"
    )
    ss = t_env.create_statement_set()
    ss.add_insert(ins_cfg["table.name"], ode_ins)
    ss.add_insert(det_cfg["table.name"], ode_det)
    ss.add_insert(mea_cfg["table.name"], ode_mea)
    ss.attach_as_datastream()
    execute(env, "VehicleInspection: canonical -> vehicle_inspection + detail + measurement")
