from pyflink.table import Schema, DataTypes


def consumer_employee_canonical_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("employeeIdentifier", DataTypes.STRING().not_null())
        .column("fullName", DataTypes.STRING())
        .column("employeeTypeName", DataTypes.STRING())
        .column("storeCode", DataTypes.STRING())
        .column("employmentStatusCode", DataTypes.STRING())
        .column("effectiveStartDate", DataTypes.STRING())
        .column("effectiveTerminationDate", DataTypes.STRING())
        .column("positionName", DataTypes.STRING())
        .column("positionJobCode", DataTypes.STRING())
        .column("originalHireDate", DataTypes.STRING())
        .build()
    )


def producer_employee_schema_builder():
    return (
        Schema.new_builder()
        .column("kafkaKey", DataTypes.STRING().not_null())
        .column("employeeIdentifier", DataTypes.STRING().not_null())
        .column("fullName", DataTypes.STRING())
        .column("employeeTypeName", DataTypes.STRING())
        .column("storeCode", DataTypes.STRING())
        .column("employmentStatusCode", DataTypes.STRING())
        .column("positionEffectiveStartDate", DataTypes.STRING())
        .column("effectiveTerminationDate", DataTypes.STRING())
        .column("positionName", DataTypes.STRING())
        .column("positionJobCode", DataTypes.STRING())
        .column("originalHireDate", DataTypes.STRING())
        .build()
    )
