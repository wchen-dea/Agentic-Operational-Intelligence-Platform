from pyflink.table import DataTypes
from pyflink.table.udf import udtf


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.INT().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.FLOAT(),
        DataTypes.FLOAT(),
        DataTypes.FLOAT(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.STRING(),
    ]
)
def extract_receipt_line_items(sor_id, line_items):
    for li in line_items or []:
        kafka_key = sor_id + "|" + str(li.salesOrderReceiptLineItemNumber)
        yield (
            kafka_key,
            sor_id,
            li.salesOrderReceiptLineItemNumber,
            li.articleNumber,
            li.soldQuantity,
            li.retailPrice,
            li.netPrice,
            li.adjustmentTypeCode,
            li.returnReasonCode,
            li.salesOrderReceiptLineItemTypeCode,
        )


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.INT().not_null(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.FLOAT(),
    ]
)
def extract_receipt_payments(sor_id, payments):
    for pay in payments or []:
        kafka_key = sor_id + "|" + str(pay.paymentId)
        yield (
            kafka_key,
            sor_id,
            pay.paymentId,
            pay.salesOrderReceiptPaymentTypeCode,
            pay.paymentTypeDescription,
            pay.paymentAmount,
        )


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.INT(),
        DataTypes.STRING(),
        DataTypes.FLOAT(),
        DataTypes.STRING(),
    ]
)
def extract_receipt_promotions(sor_id, promotions):
    for prm in promotions or []:
        kafka_key = sor_id + "|" + prm.headerPromotionTypeCode
        yield (
            kafka_key,
            sor_id,
            prm.headerPromotionTypeCode,
            prm.salesOrderLineItemPromotionNumber,
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
def extract_receipt_li_fees(sor_id, line_items):
    for li in line_items or []:
        for fee in li.fees or []:
            kafka_key = sor_id + "|" + str(li.salesOrderReceiptLineItemNumber) + "|" + fee.lineItemFeeTypeCode
            yield (
                kafka_key,
                sor_id,
                li.salesOrderReceiptLineItemNumber,
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
def extract_receipt_li_taxes(sor_id, line_items):
    for li in line_items or []:
        for tax in li.taxes or []:
            kafka_key = sor_id + "|" + str(li.salesOrderReceiptLineItemNumber) + "|" + tax.lineItemTaxTypeCode
            yield (
                kafka_key,
                sor_id,
                li.salesOrderReceiptLineItemNumber,
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
def extract_receipt_li_promos(sor_id, line_items):
    for li in line_items or []:
        for prm in li.promotions or []:
            kafka_key = sor_id + "|" + str(li.salesOrderReceiptLineItemNumber) + "|" + prm.lineItemPromotionTypeCode
            yield (
                kafka_key,
                sor_id,
                li.salesOrderReceiptLineItemNumber,
                prm.lineItemPromotionTypeCode,
                prm.lineItemPromotionTypeDescription,
                prm.lineItemPromotionAmount,
                prm.lineItemPromotionArticleNumber,
            )
