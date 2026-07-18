"""Module for schema builders."""

from pyflink.table import Schema, DataTypes


def consumer_site_canonical_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("siteNumber", DataTypes.STRING().not_null())
        .column("siteDescription", DataTypes.STRING())
        .column("siteName", DataTypes.STRING())
        .column("siteTypeCode", DataTypes.STRING())
        .column("businessUnitCode", DataTypes.STRING())
        .column("businessUnitName", DataTypes.STRING())
        .column("companyCode", DataTypes.STRING())
        .column("internalVendorNumber", DataTypes.STRING())
        .column("internalCustomerNumber", DataTypes.STRING())
        .column("regionCode", DataTypes.STRING())
        .column("E3RegionCode", DataTypes.STRING())
        .column("openDate", DataTypes.STRING())
        .column("openIndicator", DataTypes.STRING())
        .column("storeSalesCloseDate", DataTypes.STRING())
        .column("storeGeneralLedgerCloseDate", DataTypes.STRING())
        .column("storeBusinessCloseDate", DataTypes.STRING())
        .column("temporaryCloseDate", DataTypes.STRING())
        .column("reopenForBusinessDate", DataTypes.STRING())
        .column("blockingReasonCode", DataTypes.STRING())
        .column("blockingReasonDescription", DataTypes.STRING())
        .column("distributionChannelCode", DataTypes.STRING())
        .column("timeZoneCode", DataTypes.STRING())
        .build()
    )


def producer_site_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("siteNumber", DataTypes.STRING().not_null())
        .column("siteName", DataTypes.STRING())
        .column("siteDescription", DataTypes.STRING())
        .column("siteTypeCode", DataTypes.STRING())
        .column("businessUnitCode", DataTypes.STRING())
        .column("businessUnitName", DataTypes.STRING())
        .column("companyCode", DataTypes.STRING())
        .column("internalVendorNumber", DataTypes.STRING())
        .column("internalCustomerNumber", DataTypes.STRING())
        .column("regionCode", DataTypes.STRING())
        .column("e3RegionCode", DataTypes.STRING())
        .column("openDate", DataTypes.STRING())
        .column("openIndicator", DataTypes.STRING())
        .column("storeSalesCloseDate", DataTypes.STRING())
        .column("blockingReasonCode", DataTypes.STRING())
        .column("blockingReasonDescription", DataTypes.STRING())
        .column("distributionChannelCode", DataTypes.STRING())
        .column("timeZoneCode", DataTypes.STRING())
        .build()
    )
