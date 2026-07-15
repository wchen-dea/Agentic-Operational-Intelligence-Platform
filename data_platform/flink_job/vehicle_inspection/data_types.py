from pyflink.table import DataTypes


def get_tire_inspection_details():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("tirePositionCode", DataTypes.STRING().not_null()),
                DataTypes.FIELD("DOTNumber", DataTypes.STRING()),
                DataTypes.FIELD("recallIndicator", DataTypes.BOOLEAN()),
                DataTypes.FIELD("tireServicesPerformed", DataTypes.STRING()),
                DataTypes.FIELD("tireAge", DataTypes.DOUBLE()),
                DataTypes.FIELD("tireStatus", DataTypes.STRING()),
                DataTypes.FIELD(
                    "tireInspectionMeasurements",
                    DataTypes.ARRAY(
                        DataTypes.ROW(
                            [
                                DataTypes.FIELD("measurementLocation", DataTypes.STRING()),
                                DataTypes.FIELD("measurementValue", DataTypes.STRING()),
                            ]
                        )
                    ),
                ),
            ]
        )
    )
