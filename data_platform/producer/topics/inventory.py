"""Producer: CanonicalWarehouseInventorySnapshot"""

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import *


class InventoryProducer(AvroKafkaProducer):
    TOPIC = "CanonicalWarehouseInventorySnapshot"
    SCHEMA_FILE = "warehouse.inventory.snapshot.avsc"

    def generate(self):
        site = rand_store()
        article = rand_article()
        on_hand = random.randint(0, 40)
        reserved = random.randint(0, min(on_hand, 5))
        avail = max(0, on_hand - reserved)
        return {
            "kafkaKey": f"{site}|{article}",
            "siteNumber": site,
            "articleNumber": article,
            "inventoryDateTime": now_ts(),
            "onHandQuantity": on_hand,
            "reservedQuantity": reserved,
            "availableQuantity": avail,
            "inTransitQuantity": random.randint(0, 10),
            "layawayQuantity": random.randint(0, 3),
            "weborderQuantity": random.randint(0, 5),
            "purchaseDecisionCode": random.choice(["A", "B", "C", "NL"]),
            "purchaseDecisionDescription": random.choice(["Active", "Build", "Clear", "No List"]),
            "timeOffset": rand_time_offset(),
        }
