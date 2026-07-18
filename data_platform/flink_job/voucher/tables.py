"""Module for tables."""

from pyflink.table import TableDescriptor

from config import is_aws


def create_input_kafka_table(s_t_env, schema_builder, prop_config):
    base = (
        TableDescriptor.for_connector("kafka")
        .schema(schema_builder)
        .option("topic", prop_config["topic.name"])
        .option("properties.bootstrap.servers", prop_config["bootstrap.servers"])
        .option("properties.group.id", prop_config["group.id"])
        .option("scan.startup.mode", prop_config.get("scan.startup.mode", "earliest-offset"))
        .option("properties.security.protocol", prop_config.get("security.protocol", "PLAINTEXT"))
        .option("scan.topic-partition-discovery.interval", "10000")
        .option("properties.request.timeout.ms", "60000")
        .option("value.format", "avro-confluent")
        .option("value.fields-include", "EXCEPT_KEY")
        .option("key.format", "raw")
        .option("key.fields", "kafkaKey")
        .option("avro-confluent.url", prop_config["sr.url"])
        .format("avro-confluent")
    )
    return s_t_env.create_temporary_table(
        prop_config["table.name"],
        _inject_security(base),
    )


def create_output_kafka_table(s_t_env, schema_builder, prop_config):
    base = (
        TableDescriptor.for_connector("kafka")
        .schema(schema_builder)
        .option("topic", prop_config["topic.name"])
        .option("properties.bootstrap.servers", prop_config["bootstrap.servers"])
        .option("properties.security.protocol", prop_config.get("security.protocol", "PLAINTEXT"))
        .option("value.format", "avro-confluent")
        .option("value.fields-include", "EXCEPT_KEY")
        .option("key.format", "raw")
        .option("key.fields", "kafkaKey")
        .option("avro-confluent.url", prop_config["sr.url"])
        .format("avro-confluent")
    )
    return s_t_env.create_temporary_table(
        prop_config["table.name"],
        _inject_security(base),
    )


def _inject_security(descriptor):
    if is_aws():
        return (
            descriptor.option("properties.sasl.mechanism", "AWS_MSK_IAM")
            .option("properties.sasl.jaas.config", "software.amazon.msk.auth.iam.IAMLoginModule required;")
            .option(
                "properties.sasl.client.callback.handler.class", "software.amazon.msk.auth.iam.IAMClientCallbackHandler"
            )
            .build()
        )
    return descriptor.build()
