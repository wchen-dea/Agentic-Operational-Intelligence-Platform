"""Shared fake data helpers for all canonical topic producers.

Provides stable pools of domain identifiers so cross-topic records are
correlated (e.g. a work order references a real appointment identifier).
"""

from __future__ import annotations

import random
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Stable reference pools - generated once at import time
# ---------------------------------------------------------------------------

random.seed(42)

STORE_IDS = ["245", "101", "312", "408", "517", "623", "730", "841", "952", "063"]
STORE_CODES = [f"STORE{s}" for s in STORE_IDS]
REGION_CODES = ["PHX", "DAL", "DEN", "ATL", "CHI", "LAX", "NYC", "SEA", "MIA", "HOU"]
SITE_TO_REGION = {s: REGION_CODES[i % len(REGION_CODES)] for i, s in enumerate(STORE_IDS)}

CUSTOMER_IDS = [str(uuid.uuid4())[:14] for _ in range(500)]
VEHICLE_IDS = [str(uuid.uuid4())[:14] for _ in range(200)]
EMPLOYEE_IDS = [f"EMP{random.randint(10000, 99999)}" for _ in range(100)]
PERSON_NUMS = [f"P{random.randint(100000, 999999)}" for _ in range(80)]
ARTICLE_NUMS = [f"ART{random.randint(10000000, 99999999)}" for _ in range(150)]
CUSTOMER_VEHICLE_IDS = [f"CVM{random.randint(100000, 999999)}" for _ in range(300)]
TRIM_IDS = [f"TRM{random.randint(100000, 999999)}" for _ in range(180)]
ASSEMBLY_IDS = ["01", "02", "03"]

EMPLOYEE_TO_PERSON_NUM = {
    emp: PERSON_NUMS[i % len(PERSON_NUMS)]
    for i, emp in enumerate(EMPLOYEE_IDS)
}

CUSTOMER_TO_STORE: dict[str, str] = {}
STORE_TO_CUSTOMERS: dict[str, list[str]] = {}


def rebuild_customer_store_map() -> None:
    global CUSTOMER_TO_STORE, STORE_TO_CUSTOMERS

    if not STORE_IDS:
        CUSTOMER_TO_STORE = {}
        STORE_TO_CUSTOMERS = {}
        return

    mapping: dict[str, str] = {}
    for idx, customer_id in enumerate(CUSTOMER_IDS):
        mapping[customer_id] = STORE_IDS[idx % len(STORE_IDS)]

    grouped: dict[str, list[str]] = {store_id: [] for store_id in STORE_IDS}
    for customer_id, store_id in mapping.items():
        grouped.setdefault(store_id, []).append(customer_id)

    CUSTOMER_TO_STORE = mapping
    STORE_TO_CUSTOMERS = grouped


rebuild_customer_store_map()

VEHICLE_MAKES = ["Toyota", "Ford", "Chevrolet", "Honda", "Nissan", "BMW", "Mercedes", "Hyundai", "Kia", "Subaru"]
VEHICLE_MODELS = {
    "Toyota": ["Camry", "Corolla", "RAV4", "Tundra", "Tacoma"],
    "Ford": ["F-150", "Explorer", "Escape", "Edge", "Mustang"],
    "Chevrolet": ["Silverado", "Equinox", "Malibu", "Trax", "Tahoe"],
    "Honda": ["Accord", "Civic", "CR-V", "Pilot", "Odyssey"],
    "Nissan": ["Altima", "Sentra", "Rogue", "Pathfinder", "Frontier"],
    "BMW": ["3 Series", "5 Series", "X3", "X5", "7 Series"],
    "Mercedes": ["C-Class", "E-Class", "GLC", "GLE", "S-Class"],
    "Hyundai": ["Elantra", "Sonata", "Tucson", "Santa Fe", "Palisade"],
    "Kia": ["Optima", "Soul", "Sportage", "Sorento", "Telluride"],
    "Subaru": ["Outback", "Forester", "Impreza", "Legacy", "Crosstrek"],
}
VEHICLE_CLASSES = ["CAR", "TRUCK", "SUV", "VAN", "CROSSOVER"]

FIRST_NAMES = [
    "James",
    "Mary",
    "John",
    "Patricia",
    "Robert",
    "Jennifer",
    "Michael",
    "Linda",
    "William",
    "Barbara",
    "David",
    "Susan",
    "Richard",
    "Jessica",
    "Joseph",
    "Sarah",
    "Thomas",
    "Karen",
    "Charles",
    "Nancy",
]
LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
]

PAY_CODE_NAMES = ["Regular", "Overtime", "Holiday", "Sick", "Vacation", "Training", "Bonus", "Commission"]
PAY_CODE_TYPES = ["H", "S", "H", "S", "S", "H", "S", "S"]

TIRE_POSITIONS = ["LF", "RF", "LR", "RR", "SPARE"]
APPT_TYPES = ["walk_in", "online_booking", "phone", "referral"]
ORDER_TYPES = ["TIRE_INSTALL", "WHEEL_ALIGNMENT", "OIL_CHANGE", "BRAKE_SERVICE", "INSPECTION"]
VOUCHER_TYPES = ["CASH", "CHECK", "CREDIT_MEMO", "GIFT_CARD", "REBATE"]
BRAND_NAMES = [
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
STAFF_GROUPS = ["Store Manager", "Sales Advisor", "Technician", "Customer Service", "Warehouse"]


# ---------------------------------------------------------------------------
# Primitive generators
# ---------------------------------------------------------------------------


def uid() -> str:
    return str(uuid.uuid4())


def short_uid() -> str:
    return uid()[:18]


def now_ts(offset_seconds: int = 0) -> str:
    """ISO-8601 UTC timestamp string."""
    dt = datetime.now(tz=timezone.utc) + timedelta(seconds=offset_seconds)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def today_date(offset_days: int = 0) -> str:
    """ISO date string YYYY-MM-DD."""
    return (datetime.now(tz=timezone.utc) + timedelta(days=offset_days)).strftime("%Y-%m-%d")


def rand_ts(days_back: int = 30) -> str:
    offset = -random.randint(0, days_back * 86400)
    return now_ts(offset)


def rand_date(days_back: int = 30) -> str:
    offset = random.randint(0, days_back)
    return today_date(-offset)


def rand_store() -> str:
    return random.choice(STORE_IDS)


def rand_customer() -> str:
    return random.choice(CUSTOMER_IDS)


def rand_customer_for_store(store_id: str) -> str:
    customers = STORE_TO_CUSTOMERS.get(store_id)
    if customers:
        return random.choice(customers)
    return rand_customer()


def store_for_customer(customer_id: str) -> str | None:
    return CUSTOMER_TO_STORE.get(customer_id)


def rand_vehicle() -> str:
    return random.choice(VEHICLE_IDS)


def rand_article() -> str:
    return random.choice(ARTICLE_NUMS)


def rand_employee() -> str:
    return random.choice(EMPLOYEE_IDS)


def rand_customer_vehicle_id() -> str:
    return random.choice(CUSTOMER_VEHICLE_IDS)


def rand_trim_id() -> str:
    return random.choice(TRIM_IDS)


def rand_assembly_id() -> str:
    return random.choice(ASSEMBLY_IDS)


def person_num_for_employee(employee_id: str) -> str:
    return EMPLOYEE_TO_PERSON_NUM.get(employee_id, random.choice(PERSON_NUMS))


def person_identifier(person_num: str) -> int:
    return int(person_num.replace("P", ""))


def rand_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def rand_vin() -> str:
    chars = string.ascii_uppercase.replace("I", "").replace("O", "").replace("Q", "") + string.digits
    return "".join(random.choices(chars, k=17))


def rand_make_model() -> tuple[str, str]:
    make = random.choice(VEHICLE_MAKES)
    model = random.choice(VEHICLE_MODELS[make])
    return make, model


def rand_amount(lo: float = 50.0, hi: float = 2500.0) -> float:
    return round(random.uniform(lo, hi), 2)


def rand_time_offset() -> str:
    h = random.choice([-7, -6, -5, -4, -8])
    return f"{h:+03d}:00"


def maybe(value: Any, prob: float = 0.8) -> Any | None:
    """Return value with probability prob, else None."""
    return value if random.random() < prob else None
