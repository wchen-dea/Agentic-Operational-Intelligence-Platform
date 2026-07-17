"""Topic category definitions for synthetic producer orchestration."""

MASTER_DATA_TOPICS: tuple[str, ...] = (
    "article",
    "customer",
    "employee",
    "site",
    "vehicle",
)

TRANSACTION_DATA_TOPICS: tuple[str, ...] = (
    "appointment",
    "crewtime",
    "inventory",
    "kronos_hours",
    "sales_order_hybris",
    "sales_order",
    "sales_order_receipt",
    "vehicle_inspection",
    "voucher",
    "work_order",
)

# Topics that are currently produced but not part of master/transaction groups.
UNCATEGORIZED_TOPICS: tuple[str, ...] = ()

PRODUCER_TYPES: dict[str, tuple[str, ...]] = {
    "master_data": MASTER_DATA_TOPICS,
    "transaction_data": TRANSACTION_DATA_TOPICS,
}

