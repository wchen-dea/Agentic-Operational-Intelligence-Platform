"""Producer: CanonicalSapSalesorderDetail"""

import random

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import (
    maybe,
    now_ts,
    rand_amount,
    rand_article,
    rand_assembly_id,
    rand_customer,
    rand_customer_vehicle_id,
    rand_date,
    rand_employee,
    rand_store,
    rand_time_offset,
    rand_trim_id,
    rand_ts,
    rand_vehicle,
    short_uid,
)


class SalesOrderProducer(AvroKafkaProducer):
    TOPIC = "CanonicalSapSalesorderDetail"
    SCHEMA_FILE = "sap.salesorder.detail.avsc"

    def _line_item(self, num):
        retail = rand_amount(80, 800)
        disc = round(retail * random.uniform(0, 0.15), 2)
        net = round(retail - disc, 2)
        return {
            "salesOrderLineItemNumber": num,
            "salesOrderLineItemStatusCode": random.choice(["A", "B", "C"]),
            "salesOrderLineItemStatusDescription": random.choice(["Open", "Closed", "Pending"]),
            "articleNumber": rand_article(),
            "articleDescription": random.choice(["Tire", "Wheel", "Oil Change", "Brake Pad", "Wiper Blade"]),
            "salesOrderLineItemCreatedDate": rand_date(7),
            "soldQuantity": float(random.randint(1, 4)),
            "retailPrice": retail,
            "discountAmount": disc,
            "netPrice": net,
            "managerDeviationAmount": round(random.uniform(0, 20), 2),
            "adjustmentTypeCode": maybe(random.choice(["MAN", "AUTO", "COUP"])),
            "adjustmentTypeDescription": None,
            "returnReasonCode": None,
            "lineItemCancellationCode": None,
            "lineItemCancellationDescription": None,
            "miscArticleSizeDescription": None,
            "adjustmentArticleInstallMileage": None,
            "parentLineItemNumber": None,
            "salesOrderLineItemTypeCode": random.choice(["TIRE", "WHEEL", "SVC", "PART"]),
            "salesOrderLineItemTypeDescription": None,
            "priceReasonDescription": None,
            "certificateRedeemedQuantity": 0.0,
            "certificateRedeemedIndicator": False,
            "MVIArticleIndicator": random.random() < 0.3,
            "vehicleGenericCategory": maybe(random.choice(["TIRE", "WHEEL", "SERVICE"])),
            "vehicleGenericSubCategory": None,
            "orderReasonCode": maybe(random.choice(["NEW", "REPLACE", "WARRANTY"])),
            "orderReasonDescription": None,
            "fees": [
                {
                    "lineItemFeeTypeCode": "INSTALL",
                    "lineItemFeeTypeDescription": "Installation Fee",
                    "lineItemFeeAmount": round(random.uniform(10, 30), 2),
                }
            ],
            "taxes": [
                {
                    "lineItemTaxTypeCode": "STATE",
                    "lineItemTaxTypeDescription": "State Tax",
                    "lineItemTaxAmount": round(net * 0.085, 2),
                }
            ],
            "promotions": [],
        }

    def generate(self):
        so_id = short_uid()
        site = rand_store()
        cust_id = rand_customer()
        vehicle_id = rand_vehicle()
        n_items = random.randint(1, 4)
        ts = rand_ts(30)
        status = random.choice(["A", "B", "C", "D"])

        line_items = [self._line_item(i + 1) for i in range(n_items)]
        promotions = [
            {
                "salesOrderLineItemNumber": random.randint(1, n_items),
                "headerPromotionTypeCode": f"PROMO-{random.randint(100, 999)}",
                "headerPromotionTypeDescription": "Seasonal Discount",
                "headerPromotionAmount": round(random.uniform(5, 50), 2),
                "headerPromotionArticleNumber": maybe(rand_article()),
            }
            for _ in range(random.randint(0, 2))
        ]

        return {
            "kafkaKey": so_id,
            "salesOrderIdentifier": so_id,
            "originalSalesOrderIdentifier": None,
            "siteNumber": site,
            "profitCenterCode": site,
            "customerIdentifier": cust_id,
            "customerVehicleIdentifier": maybe(rand_customer_vehicle_id()),
            "vehicleIdentifier": maybe(vehicle_id),
            "trimIdentifier": maybe(rand_trim_id()),
            "assemblyIdentifier": maybe(rand_assembly_id()),
            "liftIdentifier": maybe(f"LIFT{random.randint(1, 8)}"),
            "salesOrderCreatedDate": rand_date(7),
            "salesOrderStatusCode": status,
            "salesOrderStatusDescription": {"A": "Active", "B": "Billed", "C": "Closed", "D": "Draft"}.get(status, ""),
            "salesOrderDocumentTypeCode": "ZOR",
            "salesOrderDocumentTypeDescription": "Standard Order",
            "distributionChannel": "10",
            "orderTransactionTypeCode": random.choice(["RG", "CR", "RE"]),
            "orderTransactionTypeDescription": random.choice(["Regular", "Credit", "Return"]),
            "lastModifyTimestamp": now_ts(),
            "quoteIndicator": "N",
            "carryoutIndicator": random.choice(["Y", "N"]),
            "posEventCode": maybe(random.choice(["CHECKOUT", "RETURN"])),
            "timeOffset": rand_time_offset(),
            "posEventDescription": None,
            "salesOrderOriginCode": random.choice(["WEB", "STORE", "PHONE"]),
            "employeeIdCreatedBy": rand_employee(),
            "employeeIdProcessedBy": maybe(rand_employee()),
            "returnTypeCode": None,
            "referenceSalesOrderIdentifier": None,
            "taxExemptCertificateNumber": None,
            "salesOrderReasonCode": None,
            "salesOrderReasonDescription": None,
            "datasphereTimestampVbak": None,
            "datasphereTimestampVbap": None,
            "datasphereTimestampVbfa": None,
            "datasphereTimestampVbuk": None,
            "datasphereTimestampVbrp": None,
            "sapRowCreationTimestampVbak": ts,
            "sapRowCreationTimestampVbap": ts,
            "sapRowCreationTimestampVbfa": None,
            "sapRowCreationTimestampVbrp": None,
            "promotions": promotions,
            "lineItems": line_items,
            "receipts": [],
        }
