"""Producer: CanonicalKronosSite"""

import random

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import maybe, rand_date

_CITIES = ["Phoenix", "Dallas", "Denver", "Atlanta", "Chicago", "Los Angeles", "Seattle", "Miami", "Houston", "Boston"]
_STATES = ["AZ", "TX", "CO", "GA", "IL", "CA", "WA", "FL", "TX", "MA"]
_REGIONS = ["PHX", "DAL", "DEN", "ATL", "CHI", "LAX", "SEA", "MIA", "HOU", "BOS"]


class SiteProducer(AvroKafkaProducer):
    TOPIC = "CanonicalKronosSite"
    SCHEMA_FILE = "kronos.site.avsc"

    def generate(self):
        site = f"{random.randint(100, 999)}"
        idx = int(site) % len(_CITIES)
        city = _CITIES[idx % len(_CITIES)]
        state = _STATES[idx % len(_STATES)]
        region = _REGIONS[idx % len(_REGIONS)]

        address = {
            "siteAddress": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Commerce', 'Industry'])} Blvd",
            "siteCityName": city,
            "siteStateCode": state,
            "siteZipCode": f"{random.randint(10000, 99999)}",
            "countryCode": "US",
            "timeZoneCode": random.choice(["MST", "CST", "EST", "PST"]),
        }
        store_obj = {
            "storeCode": site,
            "storeTypeCode": maybe(random.choice(["S", "E", "F"])),
            "storeGroupCode": f"GRP{random.randint(1, 5)}",
        }
        return {
            "kafkaKey": site,
            "siteNumber": site,
            "siteDescription": f"Store {site}",
            "siteName": f"DTC Store {site}",
            "siteTypeCode": random.choice(["RETAIL", "WAREHOUSE", "CORP"]),
            "businessUnitCode": f"BU{random.randint(1, 5)}",
            "businessUnitName": f"Business Unit {random.randint(1, 5)}",
            "companyCode": "1000",
            "internalVendorNumber": maybe(f"VEND{random.randint(10000, 99999)}"),
            "internalCustomerNumber": maybe(f"CUST{random.randint(10000, 99999)}"),
            "regionCode": region,
            "E3RegionCode": maybe(f"E3-{region}"),
            "regionName": f"{city} Region",
            "openDate": rand_date(3650),
            "openIndicator": "OPN",
            "siteCreateDate": rand_date(4000),
            "certificateOfOccupancyDate": maybe(rand_date(3600)),
            "storeSalesCloseDate": None,
            "storeGeneralLedgerCloseDate": None,
            "storeBusinessCloseDate": None,
            "temporaryCloseDate": None,
            "reopenForBusinessDate": None,
            "salesOrganizationCode": "1000",
            "purchasingOrganizationNumber": "1000",
            "divisionCode": "10",
            "localCurrencyCode": "USD",
            "taxTradeInIndicator": "Y",
            "valuationAreaCode": site,
            "ecoMinutesCode": None,
            "blockingReasonCode": random.choice(["NONE", "CLOSE", "RENO", "TEMP"]),
            "blockingReasonDescription": None,
            "storageCapacityNumber": maybe(str(random.randint(200, 2000))),
            "logisticsCalendarCode": None,
            "distributionChannelCode": "10",
            "address": address,
            "store": store_obj,
            "regionalOffice": {"regionalOfficeCode": region, "regionalOfficeName": f"{city} RO"},
            "regionalWarehouse": {"regionalWarehouseCode": f"WH{random.randint(1, 5)}"},
            "crossDock": None,
            "managedInventory": {"managedInventoryCode": random.choice(["Y", "N"])},
            "clusters": [
                {
                    "storeClusterCode": f"CLU{random.randint(1, 10)}",
                    "storeClusterName": f"Cluster {random.randint(1, 10)}",
                    "storeClusterTypeCode": random.choice(["GEO", "MKT", "OPS"]),
                }
                for _ in range(random.randint(0, 2))
            ],
        }
