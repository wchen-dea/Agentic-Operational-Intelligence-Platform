"""Module for data types."""

from pyflink.table import DataTypes


def get_receipt_line_items():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("salesOrderReceiptLineItemNumber", DataTypes.INT().not_null()),
                DataTypes.FIELD("articleNumber", DataTypes.STRING().not_null()),
                DataTypes.FIELD("soldQuantity", DataTypes.FLOAT()),
                DataTypes.FIELD("retailPrice", DataTypes.FLOAT()),
                DataTypes.FIELD("discountAmount", DataTypes.FLOAT()),
                DataTypes.FIELD("netPrice", DataTypes.FLOAT()),
                DataTypes.FIELD("adjustmentTypeCode", DataTypes.STRING()),
                DataTypes.FIELD("returnReasonCode", DataTypes.STRING()),
                DataTypes.FIELD("orderReasonCode", DataTypes.STRING()),
                DataTypes.FIELD("salesOrderReceiptLineItemTypeCode", DataTypes.STRING()),
                DataTypes.FIELD(
                    "fees",
                    DataTypes.ARRAY(
                        DataTypes.ROW(
                            [
                                DataTypes.FIELD("lineItemFeeTypeCode", DataTypes.STRING().not_null()),
                                DataTypes.FIELD("lineItemFeeTypeDescription", DataTypes.STRING()),
                                DataTypes.FIELD("lineItemFeeAmount", DataTypes.FLOAT()),
                            ]
                        )
                    ),
                ),
                DataTypes.FIELD(
                    "taxes",
                    DataTypes.ARRAY(
                        DataTypes.ROW(
                            [
                                DataTypes.FIELD("lineItemTaxTypeCode", DataTypes.STRING().not_null()),
                                DataTypes.FIELD("lineItemTaxTypeDescription", DataTypes.STRING()),
                                DataTypes.FIELD("lineItemTaxAmount", DataTypes.FLOAT()),
                            ]
                        )
                    ),
                ),
                DataTypes.FIELD(
                    "promotions",
                    DataTypes.ARRAY(
                        DataTypes.ROW(
                            [
                                DataTypes.FIELD("lineItemPromotionTypeCode", DataTypes.STRING().not_null()),
                                DataTypes.FIELD("lineItemPromotionTypeDescription", DataTypes.STRING()),
                                DataTypes.FIELD("lineItemPromotionAmount", DataTypes.FLOAT()),
                                DataTypes.FIELD("lineItemPromotionArticleNumber", DataTypes.STRING()),
                            ]
                        )
                    ),
                ),
            ]
        )
    )


def get_payments():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("paymentId", DataTypes.INT().not_null()),
                DataTypes.FIELD("salesOrderReceiptPaymentTypeCode", DataTypes.STRING()),
                DataTypes.FIELD("paymentTypeDescription", DataTypes.STRING()),
                DataTypes.FIELD("paymentAmount", DataTypes.FLOAT()),
            ]
        )
    )


def get_receipt_promotions():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("salesOrderLineItemPromotionNumber", DataTypes.INT()),
                DataTypes.FIELD("headerPromotionTypeCode", DataTypes.STRING().not_null()),
                DataTypes.FIELD("headerPromotionTypeDescription", DataTypes.STRING()),
                DataTypes.FIELD("headerPromotionAmount", DataTypes.FLOAT()),
                DataTypes.FIELD("headerPromotionArticleNumber", DataTypes.STRING()),
            ]
        )
    )
