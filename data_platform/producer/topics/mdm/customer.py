"""Producer: CanonicalSalesforceCrmCustomer"""

import random

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import (
    FIRST_NAMES,
    LAST_NAMES,
    maybe,
    now_ts,
    rand_time_offset,
    rand_ts,
    short_uid,
)


class CustomerProducer(AvroKafkaProducer):
    TOPIC = "CanonicalSalesforceCrmCustomer"
    SCHEMA_FILE = "salesforce.crm.customer.avsc"

    def generate(self):
        cust_id = f"CUST{random.randint(10000000, 99999999)}"
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        ts_create = rand_ts(365)
        is_org = random.random() < 0.15

        contacts = [
            {
                "customerContactIdentifier": short_uid(),
                "title": maybe(random.choice(["Mr", "Ms", "Dr"])),
                "firstName": first,
                "lastName": last,
                "phoneNumber": maybe(
                    f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"
                ),
                "alternatePhoneNumber": None,
                "email": maybe(f"{first.lower()}.{last.lower()}@example.com"),
                "primaryContactIndicator": True,
            }
        ]
        alternate_identifiers = [
            {
                "customerAlternateIdentifier": f"ALT-{random.randint(100000, 999999)}",
                "sourceSystemName": random.choice(["SALESFORCE", "SAP", "LEGACY"]),
            }
            for _ in range(random.randint(0, 2))
        ]
        vehicles = []
        addresses = [
            {
                "customerAddressIdentifier": short_uid(),
                "addressLine1": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Park'])} St",
                "city": random.choice(["Phoenix", "Dallas", "Denver", "Atlanta", "Chicago"]),
                "stateCode": random.choice(["AZ", "TX", "CO", "GA", "IL"]),
                "postalCode": f"{random.randint(10000, 99999)}",
                "countryCode": "US",
                "addressTypeCode": random.choice(["HOME", "WORK", "BILLING"]),
            }
        ]
        memberships = []

        return {
            "kafkaKey": cust_id,
            "customerIdentifier": cust_id,
            "customerTypeCode": "ORG" if is_org else random.choice(["RETAIL", "FLEET"]),
            "activeIndicator": random.random() < 0.92,
            "myAccountIndicator": random.random() < 0.60,
            "blockedReasonCode": None,
            "createTimestamp": ts_create,
            "lastUpdateTimestamp": now_ts(),
            "fraudulentIndicator": False,
            "draftIndicator": False,
            "offlineCreationIndicator": random.random() < 0.05,
            "emailOptInIndicator": random.random() < 0.70,
            "synchronyCardholderIndicator": random.random() < 0.30,
            "timeOffset": rand_time_offset(),
            "organizationAttribute": {
                "organizationName": f"{last} Enterprises",
                "organizationLegalName": f"{last} Enterprises LLC",
                "fleetAccount": {
                    "fleetAgentFirstName": None,
                    "fleetAgentLastName": None,
                    "fleetAgentPhoneNumber": None,
                },
            }
            if is_org
            else None,
            "personAttribute": {"firstName": first, "lastName": last, "fullName": f"{first} {last}"}
            if not is_org
            else None,
            "addresses": addresses,
            "vehicles": vehicles,
            "contacts": contacts,
            "alternateIdentifiers": alternate_identifiers,
            "memberships": memberships,
        }
