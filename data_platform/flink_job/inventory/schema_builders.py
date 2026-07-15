from pyflink.table import Schema, DataTypes


def consumer_inventory_canonical_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("siteNumber", DataTypes.STRING().not_null())
        .column("articleNumber", DataTypes.STRING().not_null())
        .column("inventoryDateTime", DataTypes.STRING())
        .column("onHandQuantity", DataTypes.INT())
        .column("reservedQuantity", DataTypes.INT())
        .column("availableQuantity", DataTypes.INT())
        .column("inTransitQuantity", DataTypes.INT())
        .column("layawayQuantity", DataTypes.INT())
        .column("weborderQuantity", DataTypes.INT())
        .column("purchaseDecisionCode", DataTypes.STRING())
        .column("purchaseDecisionDescription", DataTypes.STRING())
        .column("timeOffset", DataTypes.STRING())
        .build()
    )


def producer_inventory_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("siteNumber", DataTypes.STRING().not_null())
        .column("articleNumber", DataTypes.STRING().not_null())
        .column("inventoryDate", DataTypes.STRING())
        .column("onHandQuantity", DataTypes.INT())
        .column("reservedQuantity", DataTypes.INT())
        .column("availableQuantity", DataTypes.INT())
        .column("inTransitQuantity", DataTypes.INT())
        .column("layawayQuantity", DataTypes.INT())
        .column("weborderQuantity", DataTypes.INT())
        .column("purchaseDecisionCode", DataTypes.STRING())
        .column("purchaseDecisionDescription", DataTypes.STRING())
        .column("timeOffset", DataTypes.STRING())
        .build()
    )
