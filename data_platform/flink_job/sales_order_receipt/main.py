import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.table.expressions import col

from config import add_jars, get_application_properties, get_property_map, execute
from flink_job.sales_order_receipt.logging_util import log_message
from flink_job.sales_order_receipt.schema_builders import (
    consumer_sor_canonical_schema_builder,
    producer_sor_schema_builder,
    producer_sor_line_item_schema_builder,
    producer_sor_payment_schema_builder,
    producer_sor_promotion_schema_builder,
    producer_sor_li_fee_schema_builder,
    producer_sor_li_tax_schema_builder,
    producer_sor_li_promo_schema_builder,
)
from flink_job.sales_order_receipt.table_functions import (
    extract_receipt_line_items,
    extract_receipt_payments,
    extract_receipt_promotions,
    extract_receipt_li_fees,
    extract_receipt_li_taxes,
    extract_receipt_li_promos,
)
from flink_job.sales_order_receipt.tables import create_input_kafka_table, create_output_kafka_table

if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    add_jars(env)
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)
    props = get_application_properties()

    src_cfg = get_property_map(props, "sales_order_receipt.canonical")
    sor_cfg = get_property_map(props, "sales_order_receipt")
    li_cfg = get_property_map(props, "sales_order_receipt.line_item")
    fee_cfg = get_property_map(props, "sales_order_receipt.line_item.fee")
    tax_cfg = get_property_map(props, "sales_order_receipt.line_item.tax")
    liprm = get_property_map(props, "sales_order_receipt.line_item.promotion")
    pay_cfg = get_property_map(props, "sales_order_receipt.payment")
    prm_cfg = get_property_map(props, "sales_order_receipt.promotion")

    create_input_kafka_table(t_env, consumer_sor_canonical_schema_builder(), src_cfg)
    for schema_fn, cfg in [
        (producer_sor_schema_builder, sor_cfg),
        (producer_sor_line_item_schema_builder, li_cfg),
        (producer_sor_li_fee_schema_builder, fee_cfg),
        (producer_sor_li_tax_schema_builder, tax_cfg),
        (producer_sor_li_promo_schema_builder, liprm),
        (producer_sor_payment_schema_builder, pay_cfg),
        (producer_sor_promotion_schema_builder, prm_cfg),
    ]:
        create_output_kafka_table(t_env, schema_fn(), cfg)

    src = t_env.from_path(src_cfg["table.name"])

    ode_sor = src.select(
        col("salesOrderReceiptIdentifier").alias("kafkaKey"),
        col("salesOrderReceiptIdentifier"),
        col("salesOrderIdentifier"),
        col("salesOrderReceiptDocumentTypeCode"),
        col("salesOrderReceiptPostingDate"),
        col("siteNumber"),
        col("customerIdentifier"),
        col("vehicleIdentifier"),
        col("orderTransactionTypeCode"),
        col("orderTransactionTypeDescription"),
        col("lastModifyTimestamp").replace("Z", "").alias("lastModifyTimestamp"),
        col("salesOrderReceiptCreatedDate"),
        col("returnTypeCode"),
        col("referenceSalesOrderIdentifier"),
        col("timeOffset"),
    )

    ode_li = src.flat_map(extract_receipt_line_items(col("salesOrderReceiptIdentifier"), col("lineItems"))).alias(
        "kafkaKey",
        "salesOrderReceiptIdentifier",
        "salesOrderReceiptLineItemNumber",
        "articleNumber",
        "soldQuantity",
        "retailPrice",
        "netPrice",
        "adjustmentTypeCode",
        "returnReasonCode",
        "salesOrderReceiptLineItemTypeCode",
    )
    ode_pay = src.flat_map(extract_receipt_payments(col("salesOrderReceiptIdentifier"), col("payments"))).alias(
        "kafkaKey",
        "salesOrderReceiptIdentifier",
        "paymentId",
        "salesOrderReceiptPaymentTypeCode",
        "paymentTypeDescription",
        "paymentAmount",
    )
    ode_prm = src.flat_map(extract_receipt_promotions(col("salesOrderReceiptIdentifier"), col("promotions"))).alias(
        "kafkaKey",
        "salesOrderReceiptIdentifier",
        "headerPromotionTypeCode",
        "salesOrderLineItemPromotionNumber",
        "headerPromotionTypeDescription",
        "headerPromotionAmount",
        "headerPromotionArticleNumber",
    )
    ode_fee = src.flat_map(extract_receipt_li_fees(col("salesOrderReceiptIdentifier"), col("lineItems"))).alias(
        "kafkaKey",
        "salesOrderReceiptIdentifier",
        "salesOrderReceiptLineItemNumber",
        "lineItemFeeTypeCode",
        "lineItemFeeTypeDescription",
        "lineItemFeeAmount",
    )
    ode_tax = src.flat_map(extract_receipt_li_taxes(col("salesOrderReceiptIdentifier"), col("lineItems"))).alias(
        "kafkaKey",
        "salesOrderReceiptIdentifier",
        "salesOrderReceiptLineItemNumber",
        "lineItemTaxTypeCode",
        "lineItemTaxTypeDescription",
        "lineItemTaxAmount",
    )
    ode_liprm = src.flat_map(extract_receipt_li_promos(col("salesOrderReceiptIdentifier"), col("lineItems"))).alias(
        "kafkaKey",
        "salesOrderReceiptIdentifier",
        "salesOrderReceiptLineItemNumber",
        "lineItemPromotionTypeCode",
        "lineItemPromotionTypeDescription",
        "lineItemPromotionAmount",
        "lineItemPromotionArticleNumber",
    )

    ss = t_env.create_statement_set()
    for table, ode in [
        (sor_cfg, ode_sor),
        (li_cfg, ode_li),
        (fee_cfg, ode_fee),
        (tax_cfg, ode_tax),
        (liprm, ode_liprm),
        (pay_cfg, ode_pay),
        (prm_cfg, ode_prm),
    ]:
        ss.add_insert(table["table.name"], ode)
    ss.attach_as_datastream()
    execute(env, "SalesOrderReceipt: canonical -> receipt + line_item + fee + tax + promo + payment")
