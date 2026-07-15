-- ============================================================
-- 00  Database bootstrap
-- Runs first (alphabetical order in docker-entrypoint-initdb.d)
-- Creates the operational database and grants connect_user
-- all privileges so Kafka Connect JDBC Sink can CREATE / ALTER
-- tables via auto.create=true and auto.evolve=true.
-- ============================================================

CREATE DATABASE IF NOT EXISTS `retail_ops`
  CHARACTER SET  utf8mb4
  COLLATE        utf8mb4_unicode_ci;

-- Kafka Connect user needs full DDL + DML rights on the sink database
GRANT ALL PRIVILEGES ON `retail_ops`.* TO 'connect_user'@'%';

-- Debezium CDC user needs global replication grants to read MySQL binlog
CREATE USER IF NOT EXISTS 'debezium'@'%' IDENTIFIED BY 'debezium_pass';
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'debezium'@'%';
GRANT SELECT ON `retail_ops`.* TO 'debezium'@'%';
FLUSH PRIVILEGES;

USE `retail_ops`;
