"""Module for schema builders."""

from pyflink.table import Schema, DataTypes


def consumer_article_canonical_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("articleNumber", DataTypes.STRING().not_null())
        .column("articleDescription", DataTypes.STRING())
        .column("articleTypeCode", DataTypes.STRING())
        .column("articleUPCNumber", DataTypes.STRING())
        .column("brandIdentifier", DataTypes.STRING())
        .column("brandDescription", DataTypes.STRING())
        .column("familyIdentifier", DataTypes.STRING())
        .column("familyDescription", DataTypes.STRING())
        .column("lineIdentifier", DataTypes.STRING())
        .column("lineDescription", DataTypes.STRING())
        .column("vendorIdentifier", DataTypes.STRING())
        .column("merchandiseSegmentCode", DataTypes.STRING())
        .column("merchandiseSegmentDescription", DataTypes.STRING())
        .column("externalMerchandiseCategoryCode", DataTypes.STRING())
        .column("storeArticleSizeDescription", DataTypes.STRING())
        .column("storeArticleDescription", DataTypes.STRING())
        .column("coreMarketingIdentifier", DataTypes.STRING())
        .column("coreMarketingDescription", DataTypes.STRING())
        .column("baseUnitOfMeasure", DataTypes.STRING())
        .column("createdDate", DataTypes.STRING())
        .column("manufacturerCode", DataTypes.STRING())
        .column("manufacturerDescription", DataTypes.STRING())
        .column("articleLifecycleStatusCode", DataTypes.STRING())
        .column("articleLifecycleDescription", DataTypes.STRING())
        .column("runFlatIndicator", DataTypes.STRING())
        .column(
            "tire",
            DataTypes.ROW(
                [
                    DataTypes.FIELD("speedRatingCode", DataTypes.STRING()),
                    DataTypes.FIELD("tireCrossSectionNumber", DataTypes.STRING()),
                    DataTypes.FIELD("tireAspectRatio", DataTypes.STRING()),
                    DataTypes.FIELD("tireRimSizeNumber", DataTypes.STRING()),
                    DataTypes.FIELD("tireLoadRangeCode", DataTypes.STRING()),
                    DataTypes.FIELD("treadDepth", DataTypes.STRING()),
                    DataTypes.FIELD("tireLoadIndex", DataTypes.INT()),
                    DataTypes.FIELD("tireDiameter", DataTypes.FLOAT()),
                    DataTypes.FIELD("tractionGradeCode", DataTypes.STRING()),
                    DataTypes.FIELD("treadwearGradeCode", DataTypes.STRING()),
                    DataTypes.FIELD("productRatingDescription", DataTypes.STRING()),
                ]
            ),
        )
        .column(
            "wheel",
            DataTypes.ROW(
                [
                    DataTypes.FIELD("wheelWidthNumber", DataTypes.STRING()),
                    DataTypes.FIELD("wheelDiameterNumber", DataTypes.STRING()),
                    DataTypes.FIELD("wheelStyleCode", DataTypes.STRING()),
                    DataTypes.FIELD("wheelBoltPattern", DataTypes.STRING()),
                    DataTypes.FIELD("finishCode", DataTypes.STRING()),
                    DataTypes.FIELD("finishDescription", DataTypes.STRING()),
                ]
            ),
        )
        .build()
    )


def producer_article_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("articleNumber", DataTypes.STRING().not_null())
        .column("articleDescription", DataTypes.STRING())
        .column("articleTypeCode", DataTypes.STRING())
        .column("articleUpcNumber", DataTypes.STRING())
        .column("brandIdentifier", DataTypes.STRING())
        .column("brandDescription", DataTypes.STRING())
        .column("familyIdentifier", DataTypes.STRING())
        .column("lineIdentifier", DataTypes.STRING())
        .column("vendorIdentifier", DataTypes.STRING())
        .column("merchandiseSegmentCode", DataTypes.STRING())
        .column("merchandiseSegmentDescription", DataTypes.STRING())
        .column("externalMerchandiseCategoryCode", DataTypes.STRING())
        .column("storeArticleDescription", DataTypes.STRING())
        .column("coreMarketingIdentifier", DataTypes.STRING())
        .column("manufacturerCode", DataTypes.STRING())
        .column("manufacturerDescription", DataTypes.STRING())
        .column("articleLifecycleStatusCode", DataTypes.STRING())
        .column("speedRatingCode", DataTypes.STRING())
        .column("tireCrossSectionNumber", DataTypes.STRING())
        .column("tireAspectRatio", DataTypes.STRING())
        .column("tireRimSizeNumber", DataTypes.STRING())
        .column("tireLoadIndex", DataTypes.INT())
        .column("tireDiameter", DataTypes.FLOAT())
        .column("tractionGradeCode", DataTypes.STRING())
        .column("treadwearGradeCode", DataTypes.STRING())
        .column("productRatingDescription", DataTypes.STRING())
        .column("wheelWidthNumber", DataTypes.STRING())
        .column("wheelDiameterNumber", DataTypes.STRING())
        .column("wheelStyleCode", DataTypes.STRING())
        .column("finishCode", DataTypes.STRING())
        .column("finishDescription", DataTypes.STRING())
        .column("runFlatIndicator", DataTypes.STRING())
        .build()
    )
