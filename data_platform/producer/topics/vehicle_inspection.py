"""Producer: CanonicalTrendwellVehivleInspection"""

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import *


class VehicleInspectionProducer(AvroKafkaProducer):
    TOPIC = "CanonicalTrendwellVehivleInspection"
    SCHEMA_FILE = "trendwell.vehivle.inspection.avsc"

    def _tire_detail(self, position):
        return {
            "tirePositionCode": position,
            "DOTNumber": maybe(f"DOT{uid()[:8].upper()}"),
            "recallIndicator": random.random() < 0.02,
            "tireServicesPerformed": maybe(random.choice(["ROTATE", "BALANCE", "REPLACE"])),
            "tireAge": maybe(round(random.uniform(0, 8), 1)),
            "tireStatus": random.choice(["GOOD", "FAIR", "REPLACE"]),
            "tireInspectionMeasurements": [
                {"measurementLocation": loc, "measurementValue": str(round(random.uniform(2, 10), 1))}
                for loc in random.sample(["INNER", "CENTER", "OUTER"], k=random.randint(1, 3))
            ],
        }

    def generate(self):
        insp_id = uid()
        site = rand_store()
        make, model = rand_make_model()
        positions = random.sample(TIRE_POSITIONS, k=random.randint(2, 4))
        ts = rand_ts(7)

        return {
            "kafkaKey": insp_id,
            "inspectionIdentifier": insp_id,
            "customerIdentifier": rand_customer(),
            "VIN": maybe(rand_vin()),
            "vehicleLicensePlateNumber": maybe(
                f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(100000, 999999)}"
            ),
            "originalReasonCode": random.choice(["FLAT", "ROTATION", "PURCHASE", "INSPECTION"]),
            "reasonCode": None,
            "inspectionLocation": maybe(f"Bay {random.randint(1, 8)}"),
            "siteNumber": site,
            "storeCode": f"STORE{site}",
            "createWorkerIdentifier": rand_employee(),
            "createTimestamp": ts,
            "createBySourceName": random.choice(["WEB", "APP", "KIOSK"]),
            "lastUpdateTimestamp": now_ts(),
            "deviceIdentifier": maybe(uid()[:12]),
            "inspectionComments": None,
            "vehicleCondition": None,
            "mileageReading": maybe(random.randint(5000, 200000)),
            "kilometerReading": None,
            "rotationPattern": maybe(random.choice(["FORWARD_CROSS", "X_PATTERN", "STRAIGHT"])),
            "TPMSStatus": maybe(random.choice(["OK", "LOW", "FAULT"])),
            "spareInUseIndicator": random.random() < 0.05,
            "wheelLockIndicator": random.random() < 0.10,
            "carryOutIndicator": random.random() < 0.15,
            "replaceAllTiresIndicator": random.random() < 0.20,
            "replaceAllWheelsIndicator": random.random() < 0.05,
            "DOTCommunicationOptInIndicator": random.random() < 0.65,
            "vehicleIdentifier": maybe(rand_vehicle()),
            "vehicleYear": str(random.randint(2010, 2025)),
            "vehicleMake": make,
            "vehicleModel": model,
            "trimIdentifier": maybe(short_uid()),
            "assemblyIdentifier": maybe(random.choice(["01", "02"])),
            "chassisIdentifier": None,
            "frontAssemblyCode": None,
            "rearAssemblyCode": None,
            "dualRearWheelIndicator": False,
            "nonOEIndicator": random.random() < 0.10,
            "staggeredIndicator": random.random() < 0.05,
            "ACESVehicleIdentifier": None,
            "ACESBodyTypeCode": None,
            "ACESDriveIdentifier": None,
            "timeOffset": rand_time_offset(),
            "driverName": maybe(rand_name()),
            "driverEmail": None,
            "driverPhone": None,
            "tireInspectionDetails": [self._tire_detail(p) for p in positions],
        }
