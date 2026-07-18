"""Module for main."""

import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.table.expressions import col

from config import add_jars, get_application_properties, get_property_map, execute
from flink_job.article.logging_util import log_message
from flink_job.article.schema_builders import (
    consumer_article_canonical_schema_builder,
    producer_article_schema_builder,
)
from flink_job.article.tables import create_input_kafka_table, create_output_kafka_table

if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    add_jars(env)
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)
    props = get_application_properties()
    src_cfg = get_property_map(props, "article.canonical")
    snk_cfg = get_property_map(props, "article")
    create_input_kafka_table(t_env, consumer_article_canonical_schema_builder(), src_cfg)
    create_output_kafka_table(t_env, producer_article_schema_builder(), snk_cfg)
    src = t_env.from_path(src_cfg["table.name"])
    ode = src.select(
        col("articleNumber").alias("kafkaKey"),
        col("articleNumber"),
        col("articleDescription"),
        col("articleTypeCode"),
        col("articleUPCNumber").alias("articleUpcNumber"),
        col("brandIdentifier"),
        col("brandDescription"),
        col("familyIdentifier"),
        col("lineIdentifier"),
        col("vendorIdentifier"),
        col("merchandiseSegmentCode"),
        col("merchandiseSegmentDescription"),
        col("externalMerchandiseCategoryCode"),
        col("storeArticleDescription"),
        col("coreMarketingIdentifier"),
        col("manufacturerCode"),
        col("manufacturerDescription"),
        col("articleLifecycleStatusCode"),
        col("tire").get("speedRatingCode").alias("speedRatingCode"),
        col("tire").get("tireCrossSectionNumber").alias("tireCrossSectionNumber"),
        col("tire").get("tireAspectRatio").alias("tireAspectRatio"),
        col("tire").get("tireRimSizeNumber").alias("tireRimSizeNumber"),
        col("tire").get("tireLoadIndex").alias("tireLoadIndex"),
        col("tire").get("tireDiameter").alias("tireDiameter"),
        col("tire").get("tractionGradeCode").alias("tractionGradeCode"),
        col("tire").get("treadwearGradeCode").alias("treadwearGradeCode"),
        col("tire").get("productRatingDescription").alias("productRatingDescription"),
        col("wheel").get("wheelWidthNumber").alias("wheelWidthNumber"),
        col("wheel").get("wheelDiameterNumber").alias("wheelDiameterNumber"),
        col("wheel").get("wheelStyleCode").alias("wheelStyleCode"),
        col("wheel").get("finishCode").alias("finishCode"),
        col("wheel").get("finishDescription").alias("finishDescription"),
        col("runFlatIndicator"),
    )
    ss = t_env.create_statement_set()
    ss.add_insert(snk_cfg["table.name"], ode)
    ss.attach_as_datastream()
    execute(env, "Article: canonical -> article (tire+wheel flattened)")
