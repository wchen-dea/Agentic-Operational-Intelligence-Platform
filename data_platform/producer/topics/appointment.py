"""Producer: CanonicalSalesforceCrmAppointment"""

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import *


class AppointmentProducer(AvroKafkaProducer):
    TOPIC = "CanonicalSalesforceCrmAppointment"
    SCHEMA_FILE = "salesforce.crm.appointment.avsc"

    def generate(self):
        appt_id = short_uid()
        site = rand_store()
        cust_id = rand_customer()
        vehicle_id = rand_vehicle()
        ts_create = rand_ts(30)
        appt_type = random.choice(APPT_TYPES)
        status = random.choice(["scheduled", "confirmed", "showed", "no_show", "completed", "cancelled"])
        duration = random.choice([30.0, 45.0, 60.0, 90.0, 120.0])
        appt_date = rand_date(7)
        start_ts = rand_ts(7)
        end_ts = now_ts(int(duration * 60))

        slot_reservations = [
            {
                "slotReservationIdentifier": short_uid(),
                "slotIdentifier": short_uid(),
                "slotReservationTypeCode": random.choice(["CONFIRMED", "TENTATIVE"]),
                "createTimestamp": ts_create,
                "lastModifyTimestamp": ts_create,
            }
            for _ in range(random.randint(0, 2))
        ]
        tasks = (
            [
                {
                    "taskIdentifier": short_uid(),
                    "taskTypeCode": random.choice(["INSTALL", "BALANCE", "ROTATE"]),
                }
                for _ in range(random.randint(0, 3))
            ]
            if False
            else []
        )  # tasks schema not defined - omit

        return {
            "kafkaKey": appt_id,
            "appointmentIdentifier": appt_id,
            "appointmentNumber": f"APT{random.randint(100000, 999999)}",
            "appointmentTypeName": appt_type,
            "appointmentDate": appt_date,
            "workOrderIdentifier": short_uid(),
            "salesOrderIdentifier": short_uid(),
            "siteNumber": site,
            "customerIdentifier": cust_id,
            "customerTypeName": maybe(random.choice(["RETAIL", "FLEET", "COMMERCIAL"])),
            "customerVehicleIdentifier": maybe(short_uid()),
            "vehicleIdentifier": maybe(vehicle_id),
            "trimIdentifier": maybe(short_uid()),
            "assemblyIdentifier": maybe(random.choice(["01", "02", "03"])),
            "statusCode": status,
            "bookingOriginCode": maybe(random.choice(["WEB", "CALL", "WALKIN", "APP"])),
            "orderTypeName": maybe(random.choice(ORDER_TYPES)),
            "scheduledStartTimestamp": start_ts,
            "scheduledEndTimestamp": maybe(end_ts),
            "scheduledDuration": duration,
            "actualStartTimestamp": maybe(start_ts) if status in ("showed", "completed") else None,
            "actualEndTimestamp": maybe(end_ts) if status == "completed" else None,
            "actualDuration": maybe(duration) if status == "completed" else None,
            "createTimestamp": ts_create,
            "lastModifyTimestamp": now_ts(),
            "timeOffset": rand_time_offset(),
            "slotReservations": slot_reservations,
            "tasks": tasks,
        }
