"""Producer: CanonicalWarehouseInventoryProduct"""

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import *

_SIZES = ["P205/55R16", "P215/65R16", "P225/60R17", "P235/50R18", "LT265/70R17", "P275/55R20"]
_BRANDS = [
    "Michelin",
    "Goodyear",
    "Bridgestone",
    "Continental",
    "Pirelli",
    "Dunlop",
    "Falken",
    "Hankook",
    "Toyo",
    "BFGoodrich",
]


class ArticleProducer(AvroKafkaProducer):
    TOPIC = "CanonicalWarehouseInventoryProduct"
    SCHEMA_FILE = "warehouse.inventory.product.avsc"

    def generate(self):
        art_num = rand_article()
        brand = random.choice(_BRANDS)
        size = random.choice(_SIZES)
        parts = size.replace("P", "").split("/")
        cross = parts[0]
        aspect = parts[1].split("R")[0]
        rim = parts[1].split("R")[1]

        tire = {
            "speedRatingCode": maybe(random.choice(["H", "V", "W", "Y", "T"])),
            "tireCrossSectionNumber": cross,
            "tireAspectRatio": aspect,
            "tireRimSizeNumber": rim,
            "tireLoadRangeCode": maybe(random.choice(["B", "C", "D", "E"])),
            "mileageGrpTreadwellCode": None,
            "mileageGrpTreadwellDescription": None,
            "tireTestGrpTreadwellCode": None,
            "tireTestGrpTreadwellDescription": None,
            "treadDepth": str(random.randint(8, 12)),
            "tireLoadCapacity": str(random.randint(1200, 2200)),
            "tireLoadIndex": random.randint(85, 115),
            "tireDiameter": round(float(rim) * 1.1, 1),
            "tireConstructionCode": "R",
            "tractionGradeCode": random.choice(["A", "AA", "B"]),
            "treadwearGradeCode": str(random.choice([300, 400, 500, 600, 700])),
            "sideWallCode": random.choice(["BW", "WW", "OWL"]),
            "dtcMileageWarranty": str(random.choice([50000, 60000, 65000, 70000, 80000])),
            "manufacturerMileageWarranty": None,
            "productRatingDescription": random.choice(["GOOD", "BETTER", "BEST"]),
            "discountTireMaxWidth": None,
            "discountTireMinWidth": None,
            "vendorMaxWidth": None,
            "vendorMinWidth": None,
            "tempGradeCode": random.choice(["A", "B", "C"]),
            "primaryVnLoadIndex": None,
            "treadDesignCode": maybe(random.choice(["AS", "HT", "MT", "HP"])),
            "maxAirPressureNumber": random.choice([35, 40, 44, 51]),
            "runFlatIndicator": maybe(random.choice(["Y", "N"])),
        }
        wheel = None

        return {
            "kafkaKey": art_num,
            "articleNumber": art_num,
            "articleDescription": f"{brand} {size} {random.choice(['All-Season', 'Performance', 'Highway', 'Touring'])}",
            "articleTypeCode": "TIRE",
            "articleUPCNumber": maybe(f"{random.randint(10**11, 10**12 - 1)}"),
            "brandIdentifier": f"B{random.randint(100, 999)}",
            "brandCategoryCode": "P",
            "brandDescription": brand,
            "familyIdentifier": f"F{random.randint(10, 99)}",
            "familyDescription": random.choice(["Passenger", "Light Truck", "Performance"]),
            "lineIdentifier": f"L{random.randint(10, 99)}",
            "lineDescription": random.choice(["All-Season", "Summer", "Winter"]),
            "vendorIdentifier": f"V{random.randint(1000, 9999)}",
            "merchandiseCategoryCode": "TIRE",
            "merchandiseCategoryDescription": "Tire Products",
            "merchandiseSegmentCode": random.choice(["PAS", "LT", "PERF"]),
            "merchandiseSegmentDescription": None,
            "externalMerchandiseCategoryCode": None,
            "storeArticleSizeDescription": size,
            "storeArticleDescription": f"{brand} {size}",
            "coreMarketingIdentifier": maybe(random.choice(["GRN", "STD", "PRM"])),
            "coreMarketingDescription": None,
            "baseUnitOfMeasure": "EA",
            "createdDate": rand_date(365),
            "manufacturerCode": f"MFG{random.randint(100, 999)}",
            "manufacturerDescription": brand,
            "articleLifecycleStatusCode": random.choice(["A", "D", "O"]),
            "articleLifecycleDescription": None,
            "materialCode": "01",
            "certificateSoldIndicator": "N",
            "divisionCode": "10",
            "industrySectorCode": "A",
            "volumeUnitQuantity": "EA",
            "weightUnitQuantity": "LB",
            "grossWeight": round(random.uniform(15, 35), 1),
            "netWeight": round(random.uniform(14, 34), 1),
            "articleDeletionFlag": False,
            "articleDeletionDate": None,
            "tire": tire,
            "wheel": wheel,
        }
