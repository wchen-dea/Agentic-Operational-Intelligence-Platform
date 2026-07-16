from pyflink.table import Schema, DataTypes
from flink_job.sales_order.data_types import get_promotions, get_line_items


def consumer_sales_order_canonical_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderIdentifier", DataTypes.STRING().not_null())
        .column("siteNumber", DataTypes.STRING())
        .column("customerIdentifier", DataTypes.STRING())
        .column("customerVehicleIdentifier", DataTypes.STRING())
        .column("vehicleIdentifier", DataTypes.STRING())
        .column("trimIdentifier", DataTypes.STRING())
        .column("assemblyIdentifier", DataTypes.STRING())
        .column("salesOrderCreatedDate", DataTypes.STRING())
        .column("salesOrderStatusCode", DataTypes.STRING())
        .column("salesOrderStatusDescription", DataTypes.STRING())
        .column("salesOrderDocumentTypeCode", DataTypes.STRING())
        .column("salesOrderDocumentTypeDescription", DataTypes.STRING())
        .column("orderTransactionTypeCode", DataTypes.STRING())
        .column("orderTransactionTypeDescription", DataTypes.STRING())
        .column("lastModifyTimestamp", DataTypes.STRING())
        .column("timeOffset", DataTypes.STRING())
        .column("posEventCode", DataTypes.STRING())
        .column("posEventDescription", DataTypes.STRING())
        .column("salesOrderOriginCode", DataTypes.STRING())
        .column("employeeIdCreatedBy", DataTypes.STRING())
        .column("employeeIdProcessedBy", DataTypes.STRING())
        .column("liftIdentifier", DataTypes.STRING())
        .column("returnTypeCode", DataTypes.STRING())
        .column("referenceSalesOrderIdentifier", DataTypes.STRING())
        .column("quoteIndicator", DataTypes.STRING())
        .column("promotions", get_promotions())
        .column("lineItems", get_line_items())
        .build()
    )


def producer_sales_order_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderIdentifier", DataTypes.STRING().not_null())
        .column("siteNumber", DataTypes.STRING())
        .column("customerIdentifier", DataTypes.STRING())
        .column("customerVehicleIdentifier", DataTypes.STRING())
        .column("vehicleIdentifier", DataTypes.STRING())
        .column("trimIdentifier", DataTypes.STRING())
        .column("assemblyIdentifier", DataTypes.STRING())
        .column("salesOrderCreatedDate", DataTypes.STRING())
        .column("salesOrderStatusCode", DataTypes.STRING())
        .column("salesOrderStatusDescription", DataTypes.STRING())
        .column("salesOrderDocumentTypeCode", DataTypes.STRING())
        .column("salesOrderDocumentTypeDescription", DataTypes.STRING())
        .column("orderTransactionTypeCode", DataTypes.STRING())
        .column("orderTransactionTypeDescription", DataTypes.STRING())
        .column("lastModifyTimestamp", DataTypes.STRING())
        .column("timeOffset", DataTypes.STRING())
        .column("posEventCode", DataTypes.STRING())
        .column("posEventDescription", DataTypes.STRING())
        .column("salesOrderOriginCode", DataTypes.STRING())
        .column("createEmployeeIdentifier", DataTypes.STRING())
        .column("processorEmployeeIdentifier", DataTypes.STRING())
        .column("liftIdentifier", DataTypes.STRING())
        .column("returnTypeCode", DataTypes.STRING())
        .column("referenceSalesOrderIdentifier", DataTypes.STRING())
        .column("quoteIndicator", DataTypes.STRING())
        .build()
    )


def producer_so_line_item_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderIdentifier", DataTypes.STRING().not_null())
        .column("salesOrderLineItemNumber", DataTypes.INT().not_null())
        .column("salesOrderLineItemStatusCode", DataTypes.STRING())
        .column("articleNumber", DataTypes.STRING().not_null())
        .column("soldQuantity", DataTypes.FLOAT())
        .column("retailPrice", DataTypes.FLOAT())
        .column("discountAmount", DataTypes.FLOAT())
        .column("netPrice", DataTypes.FLOAT())
        .column("adjustmentTypeCode", DataTypes.STRING())
        .column("returnReasonCode", DataTypes.STRING())
        .column("salesOrderLineItemTypeCode", DataTypes.STRING())
        .column("orderReasonCode", DataTypes.STRING())
        .build()
    )


def producer_so_promotion_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderIdentifier", DataTypes.STRING().not_null())
        .column("salesOrderLineItemNumber", DataTypes.INT().not_null())
        .column("headerPromotionTypeCode", DataTypes.STRING().not_null())
        .column("headerPromotionTypeDescription", DataTypes.STRING())
        .column("headerPromotionAmount", DataTypes.FLOAT())
        .column("headerPromotionArticleNumber", DataTypes.STRING())
        .build()
    )


def producer_so_line_item_fee_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderIdentifier", DataTypes.STRING().not_null())
        .column("salesOrderLineItemNumber", DataTypes.INT().not_null())
        .column("lineItemFeeTypeCode", DataTypes.STRING().not_null())
        .column("lineItemFeeTypeDescription", DataTypes.STRING())
        .column("lineItemFeeAmount", DataTypes.FLOAT())
        .build()
    )


def producer_so_line_item_tax_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderIdentifier", DataTypes.STRING().not_null())
        .column("salesOrderLineItemNumber", DataTypes.INT().not_null())
        .column("lineItemTaxTypeCode", DataTypes.STRING().not_null())
        .column("lineItemTaxTypeDescription", DataTypes.STRING())
        .column("lineItemTaxAmount", DataTypes.FLOAT())
        .build()
    )


def producer_so_line_item_promotion_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderIdentifier", DataTypes.STRING().not_null())
        .column("salesOrderLineItemNumber", DataTypes.INT().not_null())
        .column("lineItemPromotionTypeCode", DataTypes.STRING().not_null())
        .column("lineItemPromotionTypeDescription", DataTypes.STRING())
        .column("lineItemPromotionAmount", DataTypes.FLOAT())
        .column("lineItemPromotionArticleNumber", DataTypes.STRING())
        .build()
    )
