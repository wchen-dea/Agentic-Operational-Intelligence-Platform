"""Module for schema builders."""

from pyflink.table import Schema, DataTypes
from flink_job.sales_order_receipt.data_types import (
    get_receipt_line_items,
    get_payments,
    get_receipt_promotions,
)


def consumer_sor_canonical_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderReceiptIdentifier", DataTypes.STRING().not_null())
        .column("salesOrderIdentifier", DataTypes.STRING())
        .column("salesOrderReceiptDocumentTypeCode", DataTypes.STRING())
        .column("salesOrderReceiptPostingDate", DataTypes.STRING())
        .column("siteNumber", DataTypes.STRING())
        .column("customerIdentifier", DataTypes.STRING())
        .column("vehicleIdentifier", DataTypes.STRING())
        .column("orderTransactionTypeCode", DataTypes.STRING())
        .column("orderTransactionTypeDescription", DataTypes.STRING())
        .column("lastModifyTimestamp", DataTypes.STRING())
        .column("salesOrderReceiptCreatedDate", DataTypes.STRING())
        .column("returnTypeCode", DataTypes.STRING())
        .column("referenceSalesOrderIdentifier", DataTypes.STRING())
        .column("timeOffset", DataTypes.STRING())
        .column("lineItems", get_receipt_line_items())
        .column("payments", get_payments())
        .column("promotions", get_receipt_promotions())
        .build()
    )


def producer_sor_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderReceiptIdentifier", DataTypes.STRING().not_null())
        .column("salesOrderIdentifier", DataTypes.STRING())
        .column("salesOrderReceiptDocumentTypeCode", DataTypes.STRING())
        .column("salesOrderReceiptPostingDate", DataTypes.STRING())
        .column("siteNumber", DataTypes.STRING())
        .column("customerIdentifier", DataTypes.STRING())
        .column("vehicleIdentifier", DataTypes.STRING())
        .column("orderTransactionTypeCode", DataTypes.STRING())
        .column("orderTransactionTypeDescription", DataTypes.STRING())
        .column("lastModifyTimestamp", DataTypes.STRING())
        .column("salesOrderReceiptCreatedDate", DataTypes.STRING())
        .column("returnTypeCode", DataTypes.STRING())
        .column("referenceSalesOrderIdentifier", DataTypes.STRING())
        .column("timeOffset", DataTypes.STRING())
        .build()
    )


def producer_sor_line_item_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderReceiptIdentifier", DataTypes.STRING().not_null())
        .column("salesOrderReceiptLineItemNumber", DataTypes.INT().not_null())
        .column("articleNumber", DataTypes.STRING().not_null())
        .column("soldQuantity", DataTypes.FLOAT())
        .column("retailPrice", DataTypes.FLOAT())
        .column("netPrice", DataTypes.FLOAT())
        .column("adjustmentTypeCode", DataTypes.STRING())
        .column("returnReasonCode", DataTypes.STRING())
        .column("salesOrderReceiptLineItemTypeCode", DataTypes.STRING())
        .build()
    )


def producer_sor_payment_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderReceiptIdentifier", DataTypes.STRING().not_null())
        .column("paymentId", DataTypes.INT().not_null())
        .column("salesOrderReceiptPaymentTypeCode", DataTypes.STRING())
        .column("paymentTypeDescription", DataTypes.STRING())
        .column("paymentAmount", DataTypes.FLOAT())
        .build()
    )


def producer_sor_promotion_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderReceiptIdentifier", DataTypes.STRING().not_null())
        .column("headerPromotionTypeCode", DataTypes.STRING().not_null())
        .column("salesOrderLineItemPromotionNumber", DataTypes.INT())
        .column("headerPromotionTypeDescription", DataTypes.STRING())
        .column("headerPromotionAmount", DataTypes.FLOAT())
        .column("headerPromotionArticleNumber", DataTypes.STRING())
        .build()
    )


def producer_sor_li_fee_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderReceiptIdentifier", DataTypes.STRING().not_null())
        .column("salesOrderReceiptLineItemNumber", DataTypes.INT().not_null())
        .column("lineItemFeeTypeCode", DataTypes.STRING().not_null())
        .column("lineItemFeeTypeDescription", DataTypes.STRING())
        .column("lineItemFeeAmount", DataTypes.FLOAT())
        .build()
    )


def producer_sor_li_tax_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderReceiptIdentifier", DataTypes.STRING().not_null())
        .column("salesOrderReceiptLineItemNumber", DataTypes.INT().not_null())
        .column("lineItemTaxTypeCode", DataTypes.STRING().not_null())
        .column("lineItemTaxTypeDescription", DataTypes.STRING())
        .column("lineItemTaxAmount", DataTypes.FLOAT())
        .build()
    )


def producer_sor_li_promo_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("salesOrderReceiptIdentifier", DataTypes.STRING().not_null())
        .column("salesOrderReceiptLineItemNumber", DataTypes.INT().not_null())
        .column("lineItemPromotionTypeCode", DataTypes.STRING().not_null())
        .column("lineItemPromotionTypeDescription", DataTypes.STRING())
        .column("lineItemPromotionAmount", DataTypes.FLOAT())
        .column("lineItemPromotionArticleNumber", DataTypes.STRING())
        .build()
    )
