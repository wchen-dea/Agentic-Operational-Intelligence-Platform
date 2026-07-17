"""Producer: CanonicalTrendwellVehivleWorkorder"""

import random

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import (
    FIRST_NAMES,
    LAST_NAMES,
    ORDER_TYPES,
    maybe,
    now_ts,
    rand_amount,
    rand_article,
    rand_assembly_id,
    rand_customer,
    rand_customer_vehicle_id,
    rand_employee,
    rand_store,
    rand_time_offset,
    rand_trim_id,
    rand_ts,
    rand_vehicle,
    rand_vin,
    short_uid,
)


class WorkOrderProducer(AvroKafkaProducer):
    TOPIC = "CanonicalTrendwellVehivleWorkorder"
    SCHEMA_FILE = "trendwell.vehivle.workorder.avsc"

    def generate(self):
        wo_id = short_uid()
        site = rand_store()
        status = random.choice(["OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"])
        ts_in = rand_ts(7)
        ts_bay = now_ts(random.randint(300, 1800))
        ts_out = now_ts(random.randint(1800, 7200))
        emp = rand_employee()

        line_items = [
            {
                "lineItemNumber": str(i + 1),
                "articleNumber": rand_article(),
                "articleTypeCode": random.choice(["TIRE", "WHEEL", "SVC"]),
                "articleQuantity": float(random.randint(1, 4)),
                "articleUnitPriceAmount": rand_amount(80, 600),
            }
            for i in range(random.randint(1, 4))
        ]
        bay_assignments = (
            [
                {
                    "bayNumber": f"BAY{random.randint(1, 8)}",
                    "bayStartTimestamp": ts_bay,
                    "bayEndTimestamp": ts_out if status == "COMPLETED" else None,
                    "bayTotalTime": random.randint(45, 180) if status == "COMPLETED" else None,
                }
            ]
            if status in ("IN_PROGRESS", "COMPLETED")
            else []
        )
        employees = [{"employeeIdentifier": emp}]
        contact = {
            "firstName": maybe(random.choice(FIRST_NAMES)),
            "lastName": maybe(random.choice(LAST_NAMES)),
            "email": None,
            "phone": None,
        }

        return {
            "kafkaKey": wo_id,
            "workOrderIdentifier": wo_id,
            "workOrderNumber": f"WO{random.randint(1000000, 9999999)}",
            "salesOrderIdentifier": maybe(short_uid()),
            "appointmentIdentifier": maybe(short_uid()),
            "vehicleInspectionIdentifier": maybe(short_uid()),
            "siteNumber": site,
            "storeCode": f"STORE{site}",
            "customerIdentifier": maybe(rand_customer()),
            "customerVehicleIdentifier": rand_customer_vehicle_id(),
            "vehicleIdentifier": maybe(rand_vehicle()),
            "trimIdentifier": maybe(rand_trim_id()),
            "assemblyIdentifier": maybe(rand_assembly_id()),
            "vehicleMileage": maybe(str(random.randint(5000, 200000))),
            "createTimestamp": ts_in,
            "lastModifyTimestamp": now_ts(),
            "workOrderStatus": status,
            "workOrderCheckInTimestamp": ts_in,
            "latestAwaitingServiceTimestamp": None,
            "bayInTimestamp": ts_bay if status != "OPEN" else None,
            "bayOutTimestamp": ts_out if status == "COMPLETED" else None,
            "promiseTime": maybe(ts_out),
            "totalWaitTime": maybe(random.randint(5, 60)),
            "totalBayTime": maybe(random.randint(30, 180)),
            "paymentStatus": "PAID" if status == "COMPLETED" else "PENDING",
            "carryOutIndicator": random.random() < 0.15,
            "returnForServiceIndicator": random.choice(["Y", "N"]),
            "orderTypeName": random.choice(ORDER_TYPES),
            "VIN": maybe(rand_vin()),
            "reservationIdentifier": None,
            "walkInIndicator": random.choice(["Y", "N"]),
            "dropOffWaitIndicator": random.choice(["Y", "N"]),
            "delayIndicator": random.random() < 0.10,
            "delayReasonShort": None,
            "timeOffset": rand_time_offset(),
            "vehicleCategoryName": maybe(random.choice(["PASSENGER", "LIGHT TRUCK", "SUV"])),
            "vehicleSubcategoryName": None,
            "totalUnitsQuantity": float(len(line_items)),
            "workOrderType": random.choice(["STANDARD", "EXPRESS", "FLEET"]),
            "delayReasonPrimary": None,
            "delayReasonSecondary": None,
            "delayReasonTertiary": None,
            "lineItems": line_items,
            "bayAssignments": bay_assignments,
            "employees": employees,
            "contact": contact,
        }
