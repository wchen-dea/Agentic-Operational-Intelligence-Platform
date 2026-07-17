"""Producer: CanonicalSapSalesorderHybris"""

import random

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import rand_ts, short_uid, uid


class SalesOrderHybrisProducer(AvroKafkaProducer):
    TOPIC = "CanonicalSapSalesorderHybris"
    SCHEMA_FILE = "sap.salesorder.hybris.avsc"

    def generate(self):
        so_id = short_uid()
        session = f"TW-{uid()[:12].upper()}"
        items = [
            {
                "hybrisSalesOrderLineItemNumber": i + 1,
                "orderId": so_id,
                "entryNumber": str(i + 1),
                "treadwellSessionId": session,
            }
            for i in range(random.randint(1, 3))
        ]
        return {
            "kafkaKey": so_id,
            "hybrisSalesOrderIdentifier": so_id,
            "orderTreadwellSessionIdentifier": session,
            "insertDateTimestamp": rand_ts(30),
            "items": items,
        }
