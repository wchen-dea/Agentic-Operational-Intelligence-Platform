from pyflink.table import Schema, DataTypes


def consumer_voucher_canonical_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("siteNumber", DataTypes.STRING().not_null())
        .column("voucherNumber", DataTypes.STRING().not_null())
        .column("dayDate", DataTypes.STRING().not_null())
        .column("voucherType", DataTypes.STRING().not_null())
        .column("voucherTypeDescription", DataTypes.STRING())
        .column("voucherBagID", DataTypes.STRING())
        .column("voucherAmount", DataTypes.FLOAT().not_null())
        .column("employeeIdentifier", DataTypes.STRING())
        .column("voucherCategoryCode", DataTypes.STRING())
        .column("voucherCategoryDescription", DataTypes.STRING())
        .column("voucherComments", DataTypes.STRING())
        .column("rowKey", DataTypes.INT().not_null())
        .column("financialTransactionItemNumber", DataTypes.STRING().not_null())
        .build()
    )


def producer_voucher_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("voucherNumber", DataTypes.STRING().not_null())
        .column("siteNumber", DataTypes.STRING().not_null())
        .column("voucherType", DataTypes.STRING().not_null())
        .column("voucherPostedDate", DataTypes.STRING().not_null())
        .column("voucherTypeDescription", DataTypes.STRING())
        .column("voucherBagId", DataTypes.STRING())
        .column("voucherAmount", DataTypes.FLOAT().not_null())
        .column("employeeIdentifier", DataTypes.STRING())
        .column("voucherCategoryCode", DataTypes.STRING())
        .column("voucherCategoryDescription", DataTypes.STRING())
        .column("voucherComments", DataTypes.STRING())
        .column("rowKey", DataTypes.INT().not_null())
        .column("financialTransactionItemNumber", DataTypes.STRING().not_null())
        .build()
    )
