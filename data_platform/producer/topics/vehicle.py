"""Producer: CanonicalTrendwellVehivleMaster"""

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import *


class VehicleProducer(AvroKafkaProducer):
    TOPIC = "CanonicalTrendwellVehivleMaster"
    SCHEMA_FILE = "trendwell.vehivle.master.avsc"

    def generate(self):
        vid = rand_vehicle()
        make, model = rand_make_model()
        year = str(random.randint(2005, 2026))
        trims = [
            {
                "trimIdentifier": short_uid(),
                "vehicleTrimDescription": random.choice(["Base", "Sport", "Limited", "Touring", "Premier"]),
                "assemblies": [
                    {
                        "assemblyIdentifier": f"0{i + 1}",
                        "assemblyAxleType": random.choice(["4x2", "4x4", "AWD", "FWD", "RWD"]),
                        "vehicleAssemblyDescription": random.choice(["FWD", "RWD", "AWD", "4WD"]),
                        "frontTireCrossSectionNumber": float(random.choice([205, 215, 225, 235, 245, 255])),
                        "frontTireAspectRatio": float(random.choice([45, 50, 55, 60, 65, 70])),
                        "frontWheelDiameterNumber": float(random.choice([16, 17, 18, 19, 20])),
                        "axles": [{"axleType": random.choice(["FRONT", "REAR", "ALL"])}],
                    }
                    for i in range(random.randint(1, 2))
                ],
            }
            for _ in range(random.randint(1, 3))
        ]
        return {
            "kafkaKey": vid,
            "vehicleIdentifier": vid,
            "yearNumber": year,
            "makeName": make,
            "modelName": model,
            "vehicleClassCode": random.choice(VEHICLE_CLASSES),
            "trims": trims,
        }
