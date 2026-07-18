"""Module for table functions."""

from pyflink.table import DataTypes
from pyflink.table.udf import udtf


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.INT().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING(),
        DataTypes.FLOAT(),
        DataTypes.FLOAT(),
        DataTypes.FLOAT(),
        DataTypes.FLOAT(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.STRING(),
    ]
)
def extract_line_items(so_id, line_items):
    for li in line_items or []:
        kafka_key = so_id + "|" + str(li.salesOrderLineItemNumber)
        yield (
            kafka_key,
            so_id,
            li.salesOrderLineItemNumber,
            li.articleNumber,
            li.salesOrderLineItemStatusCode,
            li.soldQuantity,
            li.retailPrice,
            li.discountAmount,
            li.netPrice,
            li.adjustmentTypeCode,
            li.returnReasonCode,
            li.salesOrderLineItemTypeCode,
            li.orderReasonCode,
        )


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.INT().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING(),
        DataTypes.FLOAT(),
        DataTypes.STRING(),
    ]
)
def extract_promotions(so_id, promotions):
    for prm in promotions or []:
        kafka_key = so_id + "|" + str(prm.salesOrderLineItemNumber) + "|" + prm.headerPromotionTypeCode
        yield (
            kafka_key,
            so_id,
            prm.salesOrderLineItemNumber,
            prm.headerPromotionTypeCode,
            prm.headerPromotionTypeDescription,
            prm.headerPromotionAmount,
            prm.headerPromotionArticleNumber,
        )


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.INT().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING(),
        DataTypes.FLOAT(),
    ]
)
def extract_line_item_fees(so_id, line_items):
    for li in line_items or []:
        for fee in li.fees or []:
            kafka_key = so_id + "|" + str(li.salesOrderLineItemNumber) + "|" + fee.lineItemFeeTypeCode
            yield (
                kafka_key,
                so_id,
                li.salesOrderLineItemNumber,
                fee.lineItemFeeTypeCode,
                fee.lineItemFeeTypeDescription,
                fee.lineItemFeeAmount,
            )


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.INT().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING(),
        DataTypes.FLOAT(),
    ]
)
def extract_line_item_taxes(so_id, line_items):
    for li in line_items or []:
        for tax in li.taxes or []:
            kafka_key = so_id + "|" + str(li.salesOrderLineItemNumber) + "|" + tax.lineItemTaxTypeCode
            yield (
                kafka_key,
                so_id,
                li.salesOrderLineItemNumber,
                tax.lineItemTaxTypeCode,
                tax.lineItemTaxTypeDescription,
                tax.lineItemTaxAmount,
            )


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.INT().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING(),
        DataTypes.FLOAT(),
        DataTypes.STRING(),
    ]
)
def extract_line_item_promotions(so_id, line_items):
    for li in line_items or []:
        for prm in li.promotions or []:
            kafka_key = so_id + "|" + str(li.salesOrderLineItemNumber) + "|" + prm.lineItemPromotionTypeCode
            yield (
                kafka_key,
                so_id,
                li.salesOrderLineItemNumber,
                prm.lineItemPromotionTypeCode,
                prm.lineItemPromotionTypeDescription,
                prm.lineItemPromotionAmount,
                prm.lineItemPromotionArticleNumber,
            )
