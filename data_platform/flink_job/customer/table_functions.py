from pyflink.table import DataTypes
from pyflink.table.udf import udtf


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.STRING(),
        DataTypes.BOOLEAN(),
    ]
)
def extract_contacts(customer_identifier, contacts):
    for c in contacts or []:
        kafka_key = customer_identifier + "|" + c.customerContactIdentifier
        yield (
            kafka_key,
            c.customerContactIdentifier,
            customer_identifier,
            c.title,
            c.firstName,
            c.lastName,
            c.phoneNumber,
            c.alternatePhoneNumber,
            c.email,
            c.primaryContactIndicator,
        )


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
    ]
)
def extract_alternate_identifiers(customer_identifier, alt_ids):
    for a in alt_ids or []:
        kafka_key = customer_identifier + "|" + a.customerAlternateIdentifier
        yield (kafka_key, a.customerAlternateIdentifier, customer_identifier, a.sourceSystemName)


@udtf(
    result_types=[
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
        DataTypes.STRING().not_null(),
    ]
)
def extract_customer_vehicles(customer_identifier, vehicles):
    for v in vehicles or []:
        kafka_key = customer_identifier + "|" + v.customerVehicleIdentifier
        yield (kafka_key, v.customerVehicleIdentifier, customer_identifier, v.vehicleIdentifier)
