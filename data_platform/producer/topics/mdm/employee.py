"""Producer: CanonicalKronosEmployee"""

import random

from data_platform.producer.base import AvroKafkaProducer
from data_platform.producer.fake import FIRST_NAMES, LAST_NAMES, maybe, rand_date, rand_name


class EmployeeProducer(AvroKafkaProducer):
    TOPIC = "CanonicalKronosEmployee"
    SCHEMA_FILE = "kronos.employee.avsc"

    def generate(self):
        emp_id = f"EMP{random.randint(10000, 99999)}"
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        store = random.randint(100, 999)
        hire_date = rand_date(1825)
        return {
            "kafkaKey": emp_id,
            "employeeIdentifier": emp_id,
            "firstName": first,
            "lastName": last,
            "fullName": f"{first} {last}",
            "positionJobCode": random.choice(["MGR", "ADV", "TECH", "CSR", "WH"]),
            "positionName": random.choice(
                ["Store Manager", "Sales Advisor", "Technician", "Customer Service Rep", "Warehouse"]
            ),
            "managementLevelCode": maybe(random.choice(["L1", "L2", "L3"])),
            "managementLevelDescription": None,
            "employmentStatusCode": random.choice(["A", "T", "L"]),
            "employeeTypeName": random.choice(["FT", "PT"]),
            "storeCode": f"STORE{store}",
            "supervisorIdentifier": maybe(f"EMP{random.randint(10000, 99999)}"),
            "supervisorName": maybe(rand_name()),
            "effectiveStartDate": hire_date,
            "effectiveTerminationDate": None,
            "originalHireDate": hire_date,
            "mostRecentRehireDate": None,
            "certifications": [
                {"certificationCode": c, "certificationDescription": c.replace("_", " ").title()}
                for c in random.sample(["TIRE_TECH", "ALIGNMENT", "BRAKE", "SALES", "MGMT"], k=random.randint(0, 3))
            ],
        }
