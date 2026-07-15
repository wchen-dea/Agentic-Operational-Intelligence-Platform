#!/usr/bin/env python3
"""Register JDBC Sink connectors for all PDM MySQL tables.

Field name mapping
------------------
Flink writes Sink topics in avro-confluent format using camelCase field names.
The ChangeCase SMT (jcustenborder/kafka-connect-transform-common) automatically
converts every camelCase Avro field to snake_case before the JDBC Sink writes
to MySQL, so Avro output and PDM schema stay aligned with zero manual remapping.

Where camelCase->snake_case conversion is ambiguous (e.g. VIN, MVIArticleIndicator)
a ReplaceField$Value rename is prepended to fix those edge cases.

Environment variables
---------------------
    CONNECT_URL          Kafka Connect REST API  (default: http://kafka-connect:8083)
    SCHEMA_REGISTRY_URL  Schema Registry URL     (default: http://schema-registry:8081)
    MYSQL_URL            JDBC connection string
    MYSQL_USER           MySQL user              (default: connect_user)
    MYSQL_PASSWORD       MySQL password          (default: connect_pass)
"""

from __future__ import annotations
import json, os, sys, time, urllib.error, urllib.request

CONNECT_URL = os.environ.get("CONNECT_URL", "http://kafka-connect:8083")
SCHEMA_REGISTRY_URL = os.environ.get("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")
MYSQL_URL = os.environ.get(
    "MYSQL_URL",
    "jdbc:mysql://mysql:3306/retail_ops"
    "?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&characterEncoding=UTF-8&sessionVariables=sql_mode=''",
)
MYSQL_USER = os.environ.get("MYSQL_USER", "connect_user")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "connect_pass")
MAX_WAIT_SECONDS = 120

_CHANGE_CASE = {
    "transforms.ChangeCase.type": "com.github.jcustenborder.kafka.connect.transform.common.ChangeCase$Value",
    "transforms.ChangeCase.from": "LOWER_CAMEL",
    "transforms.ChangeCase.to": "LOWER_UNDERSCORE",
}

_BASE = {
    "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
    "key.converter": "org.apache.kafka.connect.storage.StringConverter",
    "value.converter": "io.confluent.connect.avro.AvroConverter",
    "value.converter.schema.registry.url": SCHEMA_REGISTRY_URL,
    "connection.url": MYSQL_URL,
    "connection.user": MYSQL_USER,
    "connection.password": MYSQL_PASSWORD,
    "dialect.name": "MySqlDatabaseDialect",
    "auto.create": "false",
    "auto.evolve": "true",
    "max.retries": "5",
    "errors.tolerance": "all",
    "errors.deadletterqueue.topic.name": "_dlq_connect_errors",
    "errors.deadletterqueue.topic.replication.factor": "1",
    "errors.log.enable": "true",
    "errors.log.include.messages": "true",
    **_CHANGE_CASE,
}


def _cfg(name, topic, table, insert_mode, pk_mode, pk_fields=None, transforms="ChangeCase", extra=None):
    cfg = {
        **_BASE,
        "name": name,
        "topics": topic,
        "table.name.format": table,
        "insert.mode": insert_mode,
        "pk.mode": pk_mode,
        "transforms": transforms,
    }
    if pk_fields:
        cfg["pk.fields"] = pk_fields
    if extra:
        cfg.update(extra)
    return {"name": name, "config": cfg}


_RENAME = "org.apache.kafka.connect.transforms.ReplaceField$Value"


def _connectors():
    return [
        # Appointment
        _cfg(
            "sink-jdbc-appointment", "SinkAppointment", "appointment", "upsert", "record_key", "appointment_identifier"
        ),
        _cfg(
            "sink-jdbc-appointment-slot-reservation",
            "SinkAppointmentSlotReservation",
            "appointment_slot_reservation",
            "upsert",
            "record_value",
            "appointment_identifier,slot_reservation_identifier",
        ),
        # Article / Inventory
        _cfg("sink-jdbc-article", "SinkArticle", "article", "upsert", "record_key", "article_number"),
        _cfg(
            "sink-jdbc-article-inventory",
            "SinkArticleInventory",
            "article_inventory",
            "upsert",
            "record_value",
            "site_number,article_number,inventory_date",
            transforms="RenameField,ChangeCase",
            extra={
                "transforms.RenameField.type": _RENAME,
                "transforms.RenameField.renames": "inventoryDateTime:inventory_date",
                "transforms.RenameField.include": "siteNumber,articleNumber,inventoryDateTime,onHandQuantity,"
                "reservedQuantity,availableQuantity,inTransitQuantity,"
                "layawayQuantity,weborderQuantity,purchaseDecisionCode,"
                "purchaseDecisionDescription,timeOffset",
            },
        ),
        # Crewtime -> reflexis_weekly_staff_metrics
        _cfg(
            "sink-jdbc-reflexis-weekly-staff-metrics",
            "SinkReflexisWeeklyStaffMetrics",
            "reflexis_weekly_staff_metrics",
            "upsert",
            "record_value",
            "site_number,system_store_identifier,system_department_identifier,staff_group,week_indicator,system_date_identifier",
            transforms="RenameField,ChangeCase",
            extra={
                "transforms.RenameField.type": _RENAME,
                "transforms.RenameField.renames": "dateTimestamp:create_timestamp",
                "transforms.RenameField.include": "siteNumber,systemStoreIdentifier,systemDepartmentIdentifier,"
                "staffGroup,weekIndicator,systemDateIdentifier,dateTimestamp,"
                "demandHours,systemGrossScheduledHours,systemScheduledHours,"
                "weekScheduledHours,managerGrossScheduledHours,managerScheduledHours,"
                "lastModifyTimestamp",
            },
        ),
        # Customer
        _cfg("sink-jdbc-customer", "SinkCustomer", "customer", "upsert", "record_key", "customer_identifier"),
        _cfg(
            "sink-jdbc-customer-alternate-identifier",
            "SinkCustomerAlternateIdentifier",
            "customer_alternate_identifier",
            "upsert",
            "record_key",
            "customer_alternate_identifier",
        ),
        _cfg(
            "sink-jdbc-customer-contact",
            "SinkCustomerContact",
            "customer_contact",
            "upsert",
            "record_key",
            "customer_contact_identifier",
        ),
        _cfg(
            "sink-jdbc-customer-vehicle",
            "SinkCustomerVehicle",
            "customer_vehicle",
            "upsert",
            "record_key",
            "customer_vehicle_identifier",
        ),
        # Employee
        _cfg(
            "sink-jdbc-employee",
            "SinkEmployee",
            "employee",
            "upsert",
            "record_key",
            "employee_identifier",
            transforms="RenameField,ChangeCase",
            extra={
                "transforms.RenameField.type": _RENAME,
                "transforms.RenameField.include": "employeeIdentifier,fullName,employeeTypeName,storeCode,"
                "employmentStatusCode,effectiveStartDate,effectiveTerminationDate,"
                "positionName,positionJobCode,originalHireDate",
                "transforms.RenameField.renames": "effectiveStartDate:position_effective_start_date",
            },
        ),
        # Kronos hours
        _cfg(
            "sink-jdbc-kronos-hours",
            "SinkKronosHours",
            "kronos_hours",
            "upsert",
            "record_value",
            "time_sheet_item_identifier,pay_code_name,start_timestamp_local",
        ),
        # Sales order
        _cfg(
            "sink-jdbc-sales-order", "SinkSalesOrder", "sales_order", "upsert", "record_key", "sales_order_identifier"
        ),
        _cfg(
            "sink-jdbc-sales-order-line-item",
            "SinkSalesOrderLineItem",
            "sales_order_line_item",
            "upsert",
            "record_value",
            "sales_order_identifier,sales_order_line_item_number",
        ),
        _cfg(
            "sink-jdbc-sales-order-line-item-fee",
            "SinkSalesOrderLineItemFee",
            "sales_order_line_item_fee",
            "upsert",
            "record_value",
            "sales_order_identifier,sales_order_line_item_number,line_item_fee_type_code",
        ),
        _cfg(
            "sink-jdbc-sales-order-line-item-promotion",
            "SinkSalesOrderLineItemPromotion",
            "sales_order_line_item_promotion",
            "upsert",
            "record_value",
            "sales_order_identifier,sales_order_line_item_number,line_item_promotion_type_code",
        ),
        _cfg(
            "sink-jdbc-sales-order-line-item-tax",
            "SinkSalesOrderLineItemTax",
            "sales_order_line_item_tax",
            "upsert",
            "record_value",
            "sales_order_identifier,sales_order_line_item_number,line_item_tax_type_code",
        ),
        _cfg(
            "sink-jdbc-sales-order-promotion",
            "SinkSalesOrderPromotion",
            "sales_order_promotion",
            "upsert",
            "record_value",
            "sales_order_identifier,header_promotion_type_code,sales_order_line_item_number",
        ),
        _cfg(
            "sink-jdbc-sales-order-treadwell-session",
            "SinkSalesOrderTreadwellSession",
            "sales_order_treadwell_session",
            "upsert",
            "record_key",
            "record_identifier",
        ),
        # Sales order receipt
        _cfg(
            "sink-jdbc-sales-order-receipt",
            "SinkSalesOrderReceipt",
            "sales_order_receipt",
            "upsert",
            "record_key",
            "sales_order_receipt_identifier",
            transforms="RenameField,ChangeCase",
            extra={
                "transforms.RenameField.type": _RENAME,
                "transforms.RenameField.renames": "orderTransactionTypeCode:sales_order_receipt_transaction_type_code,"
                "orderTransactionTypeDescription:sales_order_receipt_transaction_type_description",
            },
        ),
        _cfg(
            "sink-jdbc-sales-order-receipt-line-item",
            "SinkSalesOrderReceiptLineItem",
            "sales_order_receipt_line_item",
            "upsert",
            "record_value",
            "sales_order_receipt_identifier,sales_order_receipt_line_item_number",
            transforms="RenameField,ChangeCase",
            extra={
                "transforms.RenameField.type": _RENAME,
                "transforms.RenameField.renames": "MVIArticleIndicator:mvi_article_indicator",
            },
        ),
        _cfg(
            "sink-jdbc-sales-order-receipt-line-item-allocation",
            "SinkSalesOrderReceiptLineItemAllocation",
            "sales_order_receipt_line_item_allocation",
            "upsert",
            "record_value",
            "sales_order_receipt_identifier,sales_order_receipt_line_item_number,pricing_condition_code",
        ),
        _cfg(
            "sink-jdbc-sales-order-receipt-line-item-fee",
            "SinkSalesOrderReceiptLineItemFee",
            "sales_order_receipt_line_item_fee",
            "upsert",
            "record_value",
            "sales_order_receipt_identifier,sales_order_receipt_line_item_number,line_item_fee_type_code",
        ),
        _cfg(
            "sink-jdbc-sales-order-receipt-line-item-promotion",
            "SinkSalesOrderReceiptLineItemPromotion",
            "sales_order_receipt_line_item_promotion",
            "upsert",
            "record_value",
            "sales_order_receipt_identifier,sales_order_receipt_line_item_number,line_item_promotion_type_code",
        ),
        _cfg(
            "sink-jdbc-sales-order-receipt-line-item-tax",
            "SinkSalesOrderReceiptLineItemTax",
            "sales_order_receipt_line_item_tax",
            "upsert",
            "record_value",
            "sales_order_receipt_identifier,sales_order_receipt_line_item_number,line_item_tax_type_code",
        ),
        _cfg(
            "sink-jdbc-sales-order-receipt-payment",
            "SinkSalesOrderReceiptPayment",
            "sales_order_receipt_payment",
            "upsert",
            "record_value",
            "sales_order_receipt_identifier,payment_id",
            transforms="RenameField,ChangeCase",
            extra={
                "transforms.RenameField.type": _RENAME,
                "transforms.RenameField.renames": "paymentTypeCode:sales_order_receipt_payment_type_code",
            },
        ),
        _cfg(
            "sink-jdbc-sales-order-receipt-promotion",
            "SinkSalesOrderReceiptPromotion",
            "sales_order_receipt_promotion",
            "upsert",
            "record_value",
            "sales_order_receipt_identifier,header_promotion_type_code,sales_order_line_item_promotion_number",
            transforms="RenameField,ChangeCase",
            extra={
                "transforms.RenameField.type": _RENAME,
                "transforms.RenameField.renames": "salesOrderReceiptLineItemNumber:sales_order_line_item_promotion_number",
            },
        ),
        # Voucher
        _cfg(
            "sink-jdbc-voucher",
            "SinkVoucher",
            "voucher",
            "upsert",
            "record_value",
            "voucher_number,site_number,voucher_posted_date,voucher_type,row_key,financial_transaction_item_number",
            transforms="RenameField,ChangeCase",
            extra={
                "transforms.RenameField.type": _RENAME,
                "transforms.RenameField.renames": "voucherBagID:voucher_bag_id,dayDate:voucher_posted_date",
            },
        ),
        # Site / Region
        _cfg("sink-jdbc-region", "SinkRegion", "region", "upsert", "record_key", "region_code"),
        _cfg(
            "sink-jdbc-site-blocking-reason",
            "SinkSiteBlockingReason",
            "site_blocking_reason",
            "upsert",
            "record_key",
            "blocking_reason_code",
        ),
        _cfg(
            "sink-jdbc-site-business-unit",
            "SinkSiteBusinessUnit",
            "site_business_unit",
            "upsert",
            "record_key",
            "business_unit_code",
        ),
        _cfg("sink-jdbc-site", "SinkSite", "site", "upsert", "record_key", "site_number"),
        # Vehicle
        _cfg(
            "sink-jdbc-vehicle",
            "SinkVehicle",
            "vehicle",
            "upsert",
            "record_value",
            "vehicle_identifier,trim_identifier,assembly_identifier",
        ),
        _cfg(
            "sink-jdbc-vehicle-inspection",
            "SinkVehicleInspection",
            "vehicle_inspection",
            "upsert",
            "record_key",
            "inspection_identifier",
        ),
        _cfg(
            "sink-jdbc-vehicle-tire-inspection-detail",
            "SinkVehicleTireInspectionDetail",
            "vehicle_tire_inspection_detail",
            "upsert",
            "kafka",
        ),
        _cfg(
            "sink-jdbc-vehicle-tire-inspection-measurement",
            "SinkVehicleTireInspectionMeasurement",
            "vehicle_tire_inspection_measurement",
            "upsert",
            "kafka",
        ),
        # Work order
        _cfg(
            "sink-jdbc-work-order",
            "SinkWorkOrder",
            "work_order",
            "upsert",
            "record_key",
            "work_order_identifier",
            transforms="RenameField,ChangeCase",
            extra={"transforms.RenameField.type": _RENAME, "transforms.RenameField.renames": "VIN:vin"},
        ),
        _cfg(
            "sink-jdbc-work-order-bay-assignment",
            "SinkWorkOrderBayAssignment",
            "work_order_bay_assignment",
            "upsert",
            "record_value",
            "work_order_identifier,bay_number",
        ),
        _cfg(
            "sink-jdbc-work-order-employee",
            "SinkWorkOrderEmployee",
            "work_order_employee",
            "upsert",
            "record_value",
            "work_order_identifier,employee_identifier",
        ),
        _cfg("sink-jdbc-work-order-line-item", "SinkWorkOrderLineItem", "work_order_line_item", "upsert", "kafka"),
        # Security
        _cfg(
            "sink-jdbc-agg-store-security",
            "SinkAggStoreSecurity",
            "agg_store_security",
            "upsert",
            "record_value",
            "employee_login",
        ),
        _cfg("sink-jdbc-store-security", "SinkStoreSecurity", "store_security", "upsert", "kafka"),
    ]


def _http(method, path, body=None):
    url = CONNECT_URL + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, method=method, headers={"Content-Type": "application/json"} if data else {}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw) if raw.strip() else {}


def _wait_for_connect(max_wait=MAX_WAIT_SECONDS):
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{CONNECT_URL}/connectors", timeout=5) as r:
                if r.status == 200:
                    print(f"  Kafka Connect ready at {CONNECT_URL}")
                    return
        except Exception:
            pass
        print(f"  Waiting for Kafka Connect at {CONNECT_URL} ...")
        time.sleep(5)
    raise RuntimeError(f"Kafka Connect not ready within {max_wait}s")


def main():
    connectors = _connectors()
    print(f"=== Registering {len(connectors)} JDBC Sink connectors (ChangeCase: camelCase->snake_case) ===")
    _wait_for_connect()
    ok = skipped = failed = 0
    for conn in connectors:
        name = conn["name"]
        status, resp = _http("POST", "/connectors", conn)
        if status in (200, 201):
            print(f"  OK      {name:<55s}  {conn['config']['topics']} -> {conn['config']['table.name.format']}")
            ok += 1
        elif status == 409:
            print(f"  SKIP    {name}")
            skipped += 1
        else:
            print(f"  ERR {status} {name}: {resp.get('message', str(resp))[:100]}")
            failed += 1
    print(f"\nDone: {ok} registered, {skipped} skipped, {failed} failed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
