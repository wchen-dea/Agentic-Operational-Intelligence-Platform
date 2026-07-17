"""Producer: CanonicalSapSalesorderInvoice"""

import random

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import (
    maybe,
    now_ts,
    rand_amount,
    rand_article,
    rand_assembly_id,
    rand_customer_for_store,
    rand_customer_vehicle_id,
    rand_date,
    rand_store,
    rand_time_offset,
    rand_trim_id,
    rand_ts,
    rand_vehicle,
    short_uid,
    uid,
)


class SalesOrderReceiptProducer(AvroKafkaProducer):
    TOPIC = "CanonicalSapSalesorderInvoice"
    SCHEMA_FILE = "sap.salesorder.invoice.avsc"

    def _li(self, num):
        retail = rand_amount(80, 800)
        net = round(retail * random.uniform(0.80, 1.0), 2)
        return {
            "salesOrderReceiptLineItemNumber": num,
            "articleNumber": rand_article(),
            "articleDescription": random.choice(["Tire", "Wheel", "Oil Change", "Brake Pad", "Wiper Blade"]),
            "soldQuantity": random.randint(1, 4),
            "retailPrice": retail,
            "discountAmount": round(retail - net, 2),
            "netPrice": net,
            "managerDeviationAmount": round(random.uniform(0, 20), 2),
            "certificateRedeemedQuantity": 0.0,
            "MVIArticleIndicator": random.random() < 0.3,
            "DOTNumber": maybe(f"DOT{uid()[:8].upper()}"),
            "adjustmentTypeCode": None,
            "adjustmentTypeDescription": None,
            "adjustmentArticleCurrentMileage": None,
            "adjustmentArticleTreadDepth": None,
            "extendedCost": maybe(round(net * 0.6, 2)),
            "articleInstallMileage": maybe(random.randint(5000, 120000)),
            "salesOrderReceiptParentLineNumber": None,
            "itemGLChargeCode": None,
            "orderReasonCode": None,
            "orderReasonDescription": None,
            "priceReasonDescription": None,
            "returnReasonCode": None,
            "salesOrderReceiptLineItemTypeCode": "TIRE",
            "salesOrderReceiptLineItemTypeDescription": "Tire Line Item",
            "certificateRedeemedIndicator": False,
            "salesOrderLineItemNumber": num,
            "fees": [
                {
                    "lineItemFeeTypeCode": "INSTALL",
                    "lineItemFeeTypeDescription": "Install",
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
        sor_id = short_uid()
        so_id = short_uid()
        site = rand_store()
        n_li = random.randint(1, 4)
        ts = rand_ts(30)

        line_items = [self._li(i + 1) for i in range(n_li)]
        payments = [
            {
                "paymentId": 1,
                "paymentTypeCode": random.choice(["CC", "CASH", "DEBIT", "FINANCE"]),
                "paymentTypeDescription": None,
                "paymentAmount": sum(li["netPrice"] for li in line_items),
            }
        ]
        promotions = []

        return {
            "kafkaKey": sor_id,
            "salesOrderReceiptIdentifier": sor_id,
            "salesOrderIdentifier": so_id,
            "salesOrderReceiptDocumentTypeCode": "RV",
            "salesOrderReceiptDocumentTypeDescription": "Invoice",
            "salesOrderReceiptPostingDate": rand_date(7),
            "siteNumber": site,
            "profitCenterCode": site,
            "customerIdentifier": rand_customer_for_store(site),
            "customerVehicleIdentifier": maybe(rand_customer_vehicle_id()),
            "vehicleIdentifier": maybe(rand_vehicle()),
            "trimIdentifier": maybe(rand_trim_id()),
            "assemblyIdentifier": maybe(rand_assembly_id()),
            "liftIdentifier": maybe(f"LIFT{random.randint(1, 8)}"),
            "orderTransactionTypeCode": random.choice(["RG", "CR"]),
            "orderTransactionTypeDescription": random.choice(["Regular", "Credit"]),
            "lastModifyTimestamp": now_ts(),
            "salesOrderReceiptCreatedDate": rand_date(7),
            "quoteIndicator": "N",
            "carryoutIndicator": random.choice(["Y", "N"]),
            "hybrisCustomerNumber": None,
            "timeOffset": rand_time_offset(),
            "returnTypeCode": None,
            "referenceSalesOrderIdentifier": None,
            "datasphereTimestampVbrk": None,
            "datasphereTimestampVbrp": None,
            "datasphereTimestampVbak": None,
            "datasphereTimestampVbap": None,
            "sapRowCreationTimestampVbrk": ts,
            "sapRowCreationTimestampVbrp": ts,
            "sapRowCreationTimestampVbak": ts,
            "sapRowCreationTimestampVbap": ts,
            "promotions": promotions,
            "lineItems": line_items,
            "payments": payments,
        }
