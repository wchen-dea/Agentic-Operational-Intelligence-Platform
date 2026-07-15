"""Producer: CanonicalSapSalesorderVouche"""

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import *


class VoucherProducer(AvroKafkaProducer):
    TOPIC = "CanonicalSapSalesorderVouche"
    SCHEMA_FILE = "sap.salesorder.vouche.avsc"

    def generate(self):
        vnum = f"VCH{random.randint(1000000, 9999999)}"
        site = rand_store()
        vtype = random.choice(VOUCHER_TYPES)
        return {
            "kafkaKey": vnum,
            "siteNumber": site,
            "voucherNumber": vnum,
            "dayDate": rand_date(30),
            "voucherType": vtype,
            "voucherTypeDescription": vtype.replace("_", " ").title(),
            "voucherBagID": maybe(f"BAG{random.randint(1000, 9999)}"),
            "voucherAmount": rand_amount(10, 500),
            "employeeIdentifier": rand_employee(),
            "voucherCategoryCode": maybe(random.choice(["CASH", "MISC", "REBATE"])),
            "voucherCategoryDescription": None,
            "voucherComments": None,
            "rowKey": random.randint(1, 100),
            "financialTransactionItemNumber": f"FT{random.randint(10000000, 99999999)}",
        }
