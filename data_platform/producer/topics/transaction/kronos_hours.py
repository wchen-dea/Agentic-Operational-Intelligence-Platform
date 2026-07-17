"""Producer: CanonicalKronosHours"""

import random

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import (
    PAY_CODE_NAMES,
    PAY_CODE_TYPES,
    STAFF_GROUPS,
    maybe,
    now_ts,
    person_identifier,
    person_num_for_employee,
    rand_date,
    rand_employee,
    rand_name,
    rand_store,
    rand_time_offset,
    rand_ts,
    today_date,
)


class KronosHoursProducer(AvroKafkaProducer):
    TOPIC = "CanonicalKronosHours"
    SCHEMA_FILE = "kronos.hours.avsc"

    def generate(self):
        emp_id = rand_employee()
        person = person_num_for_employee(emp_id)
        pc_idx = random.randint(0, len(PAY_CODE_NAMES) - 1)
        pay_code = PAY_CODE_NAMES[pc_idx]
        pc_type = PAY_CODE_TYPES[pc_idx]
        ts_item = random.randint(100000000, 999999999)
        start_dt = rand_ts(14)
        end_dt = now_ts(random.randint(3600, 32400))
        secs = random.randint(3600, 32400)
        store = rand_store()
        apply_dt = rand_date(14)

        return {
            "kafkaKey": f"{ts_item}|{pay_code}|{start_dt}",
            "personFullName": rand_name(),
            "personNumber": person,
            "laborLevelName1": f"STORE{store}",
            "laborLevelName2": maybe(random.choice(STAFF_GROUPS)),
            "laborLevelName3": random.choice(STAFF_GROUPS),
            "laborLevelName4": None,
            "laborLevelName5": None,
            "laborLevelName6": None,
            "laborLevelName7": None,
            "laborAcctName": maybe(f"ACCT{random.randint(1000, 9999)}"),
            "payCodeName": pay_code,
            "payCodeType": pc_type,
            "isMoneyAmountSW": False,
            "timeInSeconds": str(secs),
            "moneyAmount": None,
            "wageAmount": maybe(int(round(random.uniform(15, 45) * secs / 3600))),
            "applyDate": apply_dt,
            "adjustedApplyDate": apply_dt,
            "startDTM": start_dt,
            "endDTM": end_dt,
            "homeAccountSW": True,
            "currPayPeriodStart": rand_date(7),
            "currPayPeriodEnd": rand_date(0),
            "prevPayPeriodStart": rand_date(14),
            "prevPayPeriodEnd": rand_date(7),
            "nextPayPeriodStart": today_date(0),
            "nextPayPeriodEnd": today_date(7),
            "notPaidSW": False,
            "employeeIdentifier": int(emp_id.replace("EMP", "")),
            "paycodeIdentifier": random.randint(1, 999),
            "childPayCodeIdentifier": random.randint(1, 999),
            "timeSheetItemIdentifier": ts_item,
            "wfcTotalIdentifier": random.randint(1, 99999),
            "laborAcctIdentifier": random.randint(1, 9999),
            "personIdentifier": person_identifier(person),
            "laborLevelDSC1": maybe(f"STORE{store}"),
            "laborLevelDSC2": None,
            "laborLevelDSC3": None,
            "laborLevelDSC4": None,
            "laborLevelDSC5": None,
            "laborLevelDSC6": None,
            "laborLevelDSC7": None,
            "pcVisibleToUserSW": True,
            "addTotECTotSW": True,
            "OrgPathTxt": None,
            "OrgPathDscTxt": None,
            "displayOrderNum": maybe(random.randint(1, 100)),
            "abbreviationPcChar": maybe(pay_code[:2]),
            "visibleInRptOptnSW": True,
            "timeInDays": maybe(int(secs // 86400) or None),
            "hourlyRate": maybe(int(round(random.uniform(15, 45)))),
            "accountApprovalNum": None,
            "timeOffset": rand_time_offset(),
        }
