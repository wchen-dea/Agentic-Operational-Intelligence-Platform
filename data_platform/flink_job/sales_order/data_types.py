"""Module for data types."""

from pyflink.table import DataTypes


def get_promotions():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("salesOrderLineItemNumber", DataTypes.INT()),
                DataTypes.FIELD("headerPromotionTypeCode", DataTypes.STRING().not_null()),
                DataTypes.FIELD("headerPromotionTypeDescription", DataTypes.STRING()),
                DataTypes.FIELD("headerPromotionAmount", DataTypes.FLOAT()),
                DataTypes.FIELD("headerPromotionArticleNumber", DataTypes.STRING()),
            ]
        )
    )


def get_line_items():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("salesOrderLineItemNumber", DataTypes.INT().not_null()),
                DataTypes.FIELD("salesOrderLineItemStatusCode", DataTypes.STRING()),
                DataTypes.FIELD("salesOrderLineItemStatusDescription", DataTypes.STRING()),
                DataTypes.FIELD("articleNumber", DataTypes.STRING().not_null()),
                DataTypes.FIELD("salesOrderLineItemCreatedDate", DataTypes.STRING()),
                DataTypes.FIELD("soldQuantity", DataTypes.FLOAT()),
                DataTypes.FIELD("retailPrice", DataTypes.FLOAT()),
                DataTypes.FIELD("discountAmount", DataTypes.FLOAT()),
                DataTypes.FIELD("netPrice", DataTypes.FLOAT()),
                DataTypes.FIELD("managerDeviationAmount", DataTypes.FLOAT()),
                DataTypes.FIELD("adjustmentTypeCode", DataTypes.STRING()),
                DataTypes.FIELD("adjustmentTypeDescription", DataTypes.STRING()),
                DataTypes.FIELD("returnReasonCode", DataTypes.STRING()),
                DataTypes.FIELD("lineItemCancellationCode", DataTypes.STRING()),
                DataTypes.FIELD("lineItemCancellationDescription", DataTypes.STRING()),
                DataTypes.FIELD("salesOrderLineItemTypeCode", DataTypes.STRING()),
                DataTypes.FIELD("salesOrderLineItemTypeDescription", DataTypes.STRING()),
                DataTypes.FIELD("priceReasonDescription", DataTypes.STRING()),
                DataTypes.FIELD("orderReasonCode", DataTypes.STRING()),
                DataTypes.FIELD("orderReasonDescription", DataTypes.STRING()),
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
