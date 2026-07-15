"""Producer: CanonicalKronosCrewtime"""

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import *


class CrewtimeProducer(AvroKafkaProducer):
    TOPIC = "CanonicalKronosCrewtime"
    SCHEMA_FILE = "kronos.crewtime.avsc"

    def _hours(self, base, noise=0.15):
        return round(max(0.0, base * (1 + random.gauss(0, noise))), 2)

    def generate(self):
        site = rand_store()
        store_num = random.randint(1000, 9999)
        dept = random.randint(10, 99)
        group = random.choice(STAFF_GROUPS)
        demand = self._hours(40.0)
        sched = self._hours(38.0)
        actual = self._hours(37.5)
        avail = self._hours(42.0)
        ts = rand_ts(7)
        date_id = random.randint(20240101, 20260101)

        def diff(a, b):
            return round(max(0, a - b), 2)

        def neg(a, b):
            return round(max(0, b - a), 2)

        return {
            "kafkaKey": f"{site}|{store_num}|{dept}|{group}",
            "siteNumber": site,
            "systemStoreIdentifier": store_num,
            "systemDepartmentIdentifier": dept,
            "staffGroup": group,
            "weekIndicator": maybe(random.randint(1, 52)),
            "systemDateIdentifier": date_id,
            "dateTimestamp": ts,
            "lastModifyTimestamp": now_ts(),
            "demandHours": demand,
            "availabilityHours": avail,
            "actualHoursWorked": actual,
            "actualMealBreakHours": maybe(self._hours(0.5)),
            "systemGrossScheduledHours": self._hours(sched + 0.5),
            "systemScheduledHours": sched,
            "systemScheduledMealHours": maybe(self._hours(0.5)),
            "systemScheduleEffectivenessScore": maybe(round(random.uniform(0.7, 1.0), 4)),
            "systemSurvivingShifts": maybe(float(random.randint(3, 8))),
            "systemScheduledToDemandHours": diff(sched, demand) if sched <= demand else 0,
            "systemScheduledOverDemandHours": neg(demand, sched) if sched > demand else 0,
            "systemScheduledUnderDemandHours": neg(sched, demand) if sched < demand else 0,
            "systemActualToScheduledHours": diff(actual, sched) if actual <= sched else 0,
            "systemActualOverScheduledHours": neg(sched, actual) if actual > sched else 0,
            "systemActualUnderScheduledHours": neg(actual, sched) if actual < sched else 0,
            "managerGrossScheduledHours": maybe(self._hours(sched + 0.5)),
            "managerScheduledHours": maybe(sched),
            "managerScheduledMealHours": None,
            "managerScheduleEffectivenessScore": maybe(round(random.uniform(0.65, 1.0), 4)),
            "managerSurvivingShifts": maybe(random.randint(3, 8)),
            "managerSurvivingShiftEdits": maybe(random.randint(0, 3)),
            "managerScheduledToDemandHours": None,
            "managerScheduledOverDemandHours": None,
            "managerScheduledUnderDemandHours": None,
            "managerActualToScheduledHours": None,
            "managerActualOverScheduledHours": None,
            "managerActualUnderScheduledHours": None,
            "weekGrossScheduledHours": maybe(self._hours(sched * 5)),
            "weekScheduledHours": maybe(sched * 5),
            "weekScheduledMealHours": None,
            "weekScheduleEffectivenessScore": None,
            "weekSurvivingShifts": None,
            "weekSurvivingShiftEdits": None,
            "weekScheduledToDemandHours": None,
            "weekScheduledOverDemandHours": None,
            "weekScheduledUnderDemandHours": None,
            "weekActualToScheduledHours": None,
            "weekActualOverScheduledHours": None,
            "weekActualUnderScheduledHours": None,
            "availabilityToDemandHours": diff(avail, demand) if avail <= demand else 0,
            "availabilityOverDemandHours": neg(demand, avail) if avail > demand else 0,
            "availabilityUnderDemandHours": neg(avail, demand) if avail < demand else 0,
        }
