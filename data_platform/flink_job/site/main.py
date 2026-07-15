import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.table.expressions import col

from config import add_jars, get_application_properties, get_property_map, execute
from data_platform.flink_jobs.site.logging_util import log_message
from data_platform.flink_jobs.site.schema_builders import (
    consumer_site_canonical_schema_builder,
    producer_site_schema_builder,
)
from data_platform.flink_jobs.site.tables import create_input_kafka_table, create_output_kafka_table

if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    add_jars(env)
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)
    props = get_application_properties()
    src_cfg = get_property_map(props, "site.canonical")
    snk_cfg = get_property_map(props, "site")
    create_input_kafka_table(t_env, consumer_site_canonical_schema_builder(), src_cfg)
    create_output_kafka_table(t_env, producer_site_schema_builder(), snk_cfg)
    src = t_env.from_path(src_cfg["table.name"])
    ode = src.select(
        col("siteNumber").alias("kafkaKey"),
        col("siteNumber"),
        col("siteName"),
        col("siteDescription"),
        col("siteTypeCode"),
        col("businessUnitCode"),
        col("businessUnitName"),
        col("companyCode"),
        col("internalVendorNumber"),
        col("internalCustomerNumber"),
        col("regionCode"),
        col("E3RegionCode").alias("e3RegionCode"),
        col("openDate"),
        col("openIndicator"),
        col("storeSalesCloseDate"),
        col("blockingReasonCode"),
        col("blockingReasonDescription"),
        col("distributionChannelCode"),
        col("timeZoneCode"),
    )
    ss = t_env.create_statement_set()
    ss.add_insert(snk_cfg["table.name"], ode)
    ss.attach_as_datastream()
    execute(env, "Site: canonical -> site")
