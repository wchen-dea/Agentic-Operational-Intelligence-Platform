import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.table.expressions import col

from config import add_jars, get_application_properties, get_property_map, execute
from flink_job.sales_order.logging_util import log_message
from flink_job.sales_order.schema_builders import (
    consumer_sales_order_canonical_schema_builder,
    producer_sales_order_schema_builder,
    producer_so_line_item_schema_builder,
    producer_so_promotion_schema_builder,
    producer_so_line_item_fee_schema_builder,
    producer_so_line_item_tax_schema_builder,
    producer_so_line_item_promotion_schema_builder,
)
from flink_job.sales_order.table_functions import (
    extract_line_items,
    extract_promotions,
    extract_line_item_fees,
    extract_line_item_taxes,
    extract_line_item_promotions,
)
from flink_job.sales_order.tables import create_input_kafka_table, create_output_kafka_table

if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    add_jars(env)
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)

    props = get_application_properties()
    log_message(f"Using properties: {props}", logging.INFO)

    src_cfg = get_property_map(props, "sales_order.canonical")
    so_cfg = get_property_map(props, "sales_order")
    li_cfg = get_property_map(props, "sales_order.line_item")
    prm_cfg = get_property_map(props, "sales_order.promotion")
    fee_cfg = get_property_map(props, "sales_order.line_item.fee")
    tax_cfg = get_property_map(props, "sales_order.line_item.tax")
    liprm_cfg = get_property_map(props, "sales_order.line_item.promotion")

    create_input_kafka_table(t_env, consumer_sales_order_canonical_schema_builder(), src_cfg)
    create_output_kafka_table(t_env, producer_sales_order_schema_builder(), so_cfg)
    create_output_kafka_table(t_env, producer_so_line_item_schema_builder(), li_cfg)
    create_output_kafka_table(t_env, producer_so_promotion_schema_builder(), prm_cfg)
    create_output_kafka_table(t_env, producer_so_line_item_fee_schema_builder(), fee_cfg)
    create_output_kafka_table(t_env, producer_so_line_item_tax_schema_builder(), tax_cfg)
    create_output_kafka_table(t_env, producer_so_line_item_promotion_schema_builder(), liprm_cfg)

    src = t_env.from_path(src_cfg["table.name"])

    ode_so = src.select(
        col("salesOrderIdentifier").alias("kafkaKey"),
        col("salesOrderIdentifier"),
        col("siteNumber"),
        col("customerIdentifier"),
        col("customerVehicleIdentifier"),
        col("vehicleIdentifier"),
        col("trimIdentifier"),
        col("assemblyIdentifier"),
        col("salesOrderCreatedDate"),
        col("salesOrderStatusCode"),
        col("salesOrderStatusDescription"),
        col("salesOrderDocumentTypeCode"),
        col("salesOrderDocumentTypeDescription"),
        col("orderTransactionTypeCode"),
        col("orderTransactionTypeDescription"),
        col("lastModifyTimestamp").replace("Z", "").alias("lastModifyTimestamp"),
        col("timeOffset"),
        col("posEventCode"),
        col("posEventDescription"),
        col("salesOrderOriginCode"),
        col("employeeIdCreatedBy").alias("createEmployeeIdentifier"),
        col("employeeIdProcessedBy").alias("processorEmployeeIdentifier"),
        col("liftIdentifier"),
        col("returnTypeCode"),
        col("referenceSalesOrderIdentifier"),
        col("quoteIndicator"),
    )
    ode_li = src.flat_map(extract_line_items(col("salesOrderIdentifier"), col("lineItems"))).alias(
        "kafkaKey",
        "salesOrderIdentifier",
        "salesOrderLineItemNumber",
        "articleNumber",
        "salesOrderLineItemStatusCode",
        "soldQuantity",
        "retailPrice",
        "discountAmount",
        "netPrice",
        "adjustmentTypeCode",
        "returnReasonCode",
        "salesOrderLineItemTypeCode",
        "orderReasonCode",
    )
    ode_prm = src.flat_map(extract_promotions(col("salesOrderIdentifier"), col("promotions"))).alias(
        "kafkaKey",
        "salesOrderIdentifier",
        "salesOrderLineItemNumber",
        "headerPromotionTypeCode",
        "headerPromotionTypeDescription",
        "headerPromotionAmount",
        "headerPromotionArticleNumber",
    )
    ode_fee = src.flat_map(extract_line_item_fees(col("salesOrderIdentifier"), col("lineItems"))).alias(
        "kafkaKey",
        "salesOrderIdentifier",
        "salesOrderLineItemNumber",
        "lineItemFeeTypeCode",
        "lineItemFeeTypeDescription",
        "lineItemFeeAmount",
    )
    ode_tax = src.flat_map(extract_line_item_taxes(col("salesOrderIdentifier"), col("lineItems"))).alias(
        "kafkaKey",
        "salesOrderIdentifier",
        "salesOrderLineItemNumber",
        "lineItemTaxTypeCode",
        "lineItemTaxTypeDescription",
        "lineItemTaxAmount",
    )
    ode_liprm = src.flat_map(extract_line_item_promotions(col("salesOrderIdentifier"), col("lineItems"))).alias(
        "kafkaKey",
        "salesOrderIdentifier",
        "salesOrderLineItemNumber",
        "lineItemPromotionTypeCode",
        "lineItemPromotionTypeDescription",
        "lineItemPromotionAmount",
        "lineItemPromotionArticleNumber",
    )

    ss = t_env.create_statement_set()
    ss.add_insert(so_cfg["table.name"], ode_so)
    ss.add_insert(li_cfg["table.name"], ode_li)
    ss.add_insert(prm_cfg["table.name"], ode_prm)
    ss.add_insert(fee_cfg["table.name"], ode_fee)
    ss.add_insert(tax_cfg["table.name"], ode_tax)
    ss.add_insert(liprm_cfg["table.name"], ode_liprm)
    ss.attach_as_datastream()

    execute(env, "SalesOrder: canonical -> sales_order + line_item + promotion + fee + tax + line_item_promotion")
