"""Module for data types."""

from pyflink.table import DataTypes


def get_slot_reservations():
    return DataTypes.ARRAY(
        DataTypes.ROW(
            [
                DataTypes.FIELD("slotReservationIdentifier", DataTypes.STRING().not_null()),
                DataTypes.FIELD("slotReservationTypeCode", DataTypes.STRING()),
                DataTypes.FIELD("createTimestamp", DataTypes.STRING()),
                DataTypes.FIELD("lastModifyTimestamp", DataTypes.STRING()),
            ]
        )
    )
