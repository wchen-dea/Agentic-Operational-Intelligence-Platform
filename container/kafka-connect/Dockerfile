FROM confluentinc/cp-kafka-connect:7.7.0

# Install the Confluent JDBC Sink/Source connector via confluent-hub
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:10.7.6

# Install Debezium MySQL CDC connector
RUN confluent-hub install --no-prompt debezium/debezium-connector-mysql:2.4.2

# Install ChangeCase SMT — converts camelCase Avro field names to snake_case
# MySQL column names automatically (LOWER_CAMEL → LOWER_UNDERSCORE).
RUN confluent-hub install --no-prompt jcustenborder/kafka-connect-transform-common:0.1.0.58

# Download MySQL Connector/J (JDBC driver for MySQL 8.x).
# Placed in the JDBC connector's lib directory so it is picked up at runtime.
ARG MYSQL_DRIVER_VERSION=8.3.0
RUN curl -fsSL \
    "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/${MYSQL_DRIVER_VERSION}/mysql-connector-j-${MYSQL_DRIVER_VERSION}.jar" \
    -o "/usr/share/confluent-hub-components/confluentinc-kafka-connect-jdbc/lib/mysql-connector-j-${MYSQL_DRIVER_VERSION}.jar"
