from pyflink.table import Schema, DataTypes


def consumer_crewtime_canonical_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("siteNumber", DataTypes.STRING().not_null())
        .column("systemStoreIdentifier", DataTypes.INT().not_null())
        .column("systemDepartmentIdentifier", DataTypes.INT().not_null())
        .column("staffGroup", DataTypes.STRING().not_null())
        .column("weekIndicator", DataTypes.INT())
        .column("systemDateIdentifier", DataTypes.INT().not_null())
        .column("dateTimestamp", DataTypes.STRING())
        .column("lastModifyTimestamp", DataTypes.STRING())
        .column("demandHours", DataTypes.FLOAT())
        .column("systemGrossScheduledHours", DataTypes.FLOAT())
        .column("systemScheduledHours", DataTypes.FLOAT())
        .column("weekScheduledHours", DataTypes.FLOAT())
        .column("managerGrossScheduledHours", DataTypes.FLOAT())
        .column("managerScheduledHours", DataTypes.FLOAT())
        .build()
    )


def producer_reflexis_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("siteNumber", DataTypes.STRING().not_null())
        .column("systemStoreIdentifier", DataTypes.INT().not_null())
        .column("systemDepartmentIdentifier", DataTypes.INT().not_null())
        .column("staffGroup", DataTypes.STRING().not_null())
        .column("weekIndicator", DataTypes.INT().not_null())
        .column("systemDateIdentifier", DataTypes.INT().not_null())
        .column("createTimestamp", DataTypes.STRING())
        .column("lastModifyTimestamp", DataTypes.STRING())
        .column("demandHours", DataTypes.FLOAT())
        .column("systemGrossScheduledHours", DataTypes.FLOAT())
        .column("systemScheduledHours", DataTypes.FLOAT())
        .column("weekScheduledHours", DataTypes.FLOAT())
        .column("managerGrossScheduledHours", DataTypes.FLOAT())
        .column("managerScheduledHours", DataTypes.FLOAT())
        .build()
    )
