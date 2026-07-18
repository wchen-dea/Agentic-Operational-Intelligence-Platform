"""Module for data types."""

from pyflink.table import DataTypes


def get_trims():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("trimIdentifier", DataTypes.STRING().not_null()),
                DataTypes.FIELD("vehicleTrimDescription", DataTypes.STRING()),
                DataTypes.FIELD(
                    "assemblies",
                    DataTypes.ARRAY(
                        DataTypes.ROW(
                            [
                                DataTypes.FIELD("assemblyIdentifier", DataTypes.STRING().not_null()),
                                DataTypes.FIELD("vehicleAssemblyDescription", DataTypes.STRING()),
                                DataTypes.FIELD("frontTireCrossSectionNumber", DataTypes.FLOAT()),
                                DataTypes.FIELD("frontTireAspectRatio", DataTypes.FLOAT()),
                                DataTypes.FIELD("frontWheelDiameterNumber", DataTypes.FLOAT()),
                            ]
                        )
                    ),
                ),
            ]
        )
    )
