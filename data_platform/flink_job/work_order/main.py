import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from pyflink.table.expressions import col

from config import add_jars, get_application_properties, get_property_map, execute
from flink_job.work_order.logging_util import log_message
from flink_job.work_order.schema_builders import (
    consumer_wom_canonical_schema_builder,
    producer_work_order_schema_builder,
    producer_wo_line_item_schema_builder,
    producer_wo_bay_assignment_schema_builder,
    producer_wo_employee_schema_builder,
)
from flink_job.work_order.table_functions import (
    extract_line_items,
    extract_bay_assignments,
    extract_employees,
)
from flink_job.work_order.tables import create_input_kafka_table, create_output_kafka_table

if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    add_jars(env)
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)
    props = get_application_properties()
    src_cfg = get_property_map(props, "wom.canonical")
    wo_cfg = get_property_map(props, "wom.work_order")
    li_cfg = get_property_map(props, "wom.line_item")
    ba_cfg = get_property_map(props, "wom.bay_assignment")
    emp_cfg = get_property_map(props, "wom.employee")
    create_input_kafka_table(t_env, consumer_wom_canonical_schema_builder(), src_cfg)
    create_output_kafka_table(t_env, producer_work_order_schema_builder(), wo_cfg)
    create_output_kafka_table(t_env, producer_wo_line_item_schema_builder(), li_cfg)
    create_output_kafka_table(t_env, producer_wo_bay_assignment_schema_builder(), ba_cfg)
    create_output_kafka_table(t_env, producer_wo_employee_schema_builder(), emp_cfg)
    src = t_env.from_path(src_cfg["table.name"])
    ode_wo = src.select(
        col("workOrderIdentifier").alias("kafkaKey"),
        col("workOrderIdentifier"),
        col("workOrderNumber"),
        col("orderTypeName"),
        col("salesOrderIdentifier"),
        col("appointmentIdentifier"),
        col("vehicleInspectionIdentifier"),
        col("siteNumber"),
        col("customerIdentifier"),
        col("vehicleIdentifier"),
        col("workOrderStatus"),
        col("workOrderCheckInTimestamp").replace("Z", "").alias("workOrderCheckInTimestamp"),
        col("bayInTimestamp").replace("Z", "").alias("bayInTimestamp"),
        col("bayOutTimestamp").replace("Z", "").alias("bayOutTimestamp"),
        col("VIN").alias("vin"),
        col("delayIndicator"),
        col("delayReasonShort"),
        col("contact").get("firstName").alias("contactFirstName"),
        col("contact").get("lastName").alias("contactLastName"),
        col("contact").get("email").alias("contactEmail"),
        col("contact").get("phone").alias("contactPhone"),
        col("createTimestamp").replace("Z", "").alias("createTimestamp"),
        col("lastModifyTimestamp").replace("Z", "").alias("lastModifyTimestamp"),
        col("timeOffset"),
        col("workOrderType"),
    )
    ode_li = src.flat_map(extract_line_items(col("workOrderIdentifier"), col("lineItems"))).alias(
        "kafkaKey",
        "workOrderIdentifier",
        "lineItemNumber",
        "articleNumber",
        "articleTypeCode",
        "articleQuantity",
        "articleUnitPriceAmount",
    )
    ode_ba = src.flat_map(extract_bay_assignments(col("workOrderIdentifier"), col("bayAssignments"))).alias(
        "kafkaKey", "workOrderIdentifier", "bayNumber", "bayStartTimestamp", "bayEndTimestamp", "bayTotalTime"
    )
    ode_emp = src.flat_map(extract_employees(col("workOrderIdentifier"), col("employees"))).alias(
        "kafkaKey", "workOrderIdentifier", "employeeIdentifier"
    )
    ss = t_env.create_statement_set()
    ss.add_insert(wo_cfg["table.name"], ode_wo)
    ss.add_insert(li_cfg["table.name"], ode_li)
    ss.add_insert(ba_cfg["table.name"], ode_ba)
    ss.add_insert(emp_cfg["table.name"], ode_emp)
    ss.attach_as_datastream()
    execute(env, "WorkOrder: canonical -> work_order + line_item + bay_assignment + employee")
