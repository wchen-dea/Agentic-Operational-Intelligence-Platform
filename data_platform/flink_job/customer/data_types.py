from pyflink.table import DataTypes


def get_contacts():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("customerContactIdentifier", DataTypes.STRING().not_null()),
                DataTypes.FIELD("title", DataTypes.STRING()),
                DataTypes.FIELD("firstName", DataTypes.STRING()),
                DataTypes.FIELD("lastName", DataTypes.STRING()),
                DataTypes.FIELD("phoneNumber", DataTypes.STRING()),
                DataTypes.FIELD("alternatePhoneNumber", DataTypes.STRING()),
                DataTypes.FIELD("email", DataTypes.STRING()),
                DataTypes.FIELD("primaryContactIndicator", DataTypes.BOOLEAN()),
            ]
        )
    )


def get_alternate_identifiers():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("customerAlternateIdentifier", DataTypes.STRING().not_null()),
                DataTypes.FIELD("sourceSystemName", DataTypes.STRING().not_null()),
            ]
        )
    )


def get_vehicles():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("customerVehicleIdentifier", DataTypes.STRING().not_null()),
                DataTypes.FIELD("vehicleIdentifier", DataTypes.STRING().not_null()),
            ]
        )
    )
