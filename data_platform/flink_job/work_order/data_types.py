from pyflink.table import DataTypes


def get_line_items():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("lineItemNumber", DataTypes.STRING().not_null()),
                DataTypes.FIELD("articleNumber", DataTypes.STRING()),
                DataTypes.FIELD("articleTypeCode", DataTypes.STRING()),
                DataTypes.FIELD("articleQuantity", DataTypes.DOUBLE()),
                DataTypes.FIELD("articleUnitPriceAmount", DataTypes.DOUBLE()),
            ]
        )
    )


def get_bay_assignments():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("bayNumber", DataTypes.STRING().not_null()),
                DataTypes.FIELD("bayStartTimestamp", DataTypes.STRING()),
                DataTypes.FIELD("bayEndTimestamp", DataTypes.STRING()),
                DataTypes.FIELD("bayTotalTime", DataTypes.INT()),
            ]
        )
    )


def get_employees():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("employeeIdentifier", DataTypes.STRING().not_null()),
            ]
        )
    )


def get_contact():
    return DataTypes.ROW(
        [
            DataTypes.FIELD("firstName", DataTypes.STRING()),
            DataTypes.FIELD("lastName", DataTypes.STRING()),
            DataTypes.FIELD("email", DataTypes.STRING()),
            DataTypes.FIELD("phone", DataTypes.STRING()),
        ]
    )
