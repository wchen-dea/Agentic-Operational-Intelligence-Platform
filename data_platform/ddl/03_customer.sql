-- ============================================================
-- 03  Customer tables
--     customer → customer_alternate_identifier
--                customer_contact
--                customer_vehicle
-- ============================================================

USE `retail_ops`;

CREATE TABLE IF NOT EXISTS `customer` (
  `customer_identifier`      varchar(14)  NOT NULL,
  `customer_type_code`       varchar(10)  DEFAULT NULL,
  `organization_legal_name`  varchar(50)  DEFAULT NULL,
  `ar_account_number`        varchar(50)  DEFAULT NULL,
  `fleet_account_identifier` varchar(14)  DEFAULT NULL,
  `full_name`                varchar(100) DEFAULT NULL,
  `organization_name`        varchar(50)  DEFAULT NULL,
  `create_timestamp`         datetime     NOT NULL,
  `last_modify_timestamp`    datetime     NOT NULL,
  `time_offset`              varchar(100) DEFAULT NULL,
  `db_create_timestamp`      datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`      datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`customer_identifier`),
  KEY `idx_cus_ctc` (`customer_type_code`)       COMMENT 'ORE User defined',
  KEY `idx_cus_fai` (`fleet_account_identifier`) COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `customer_alternate_identifier` (
  `customer_identifier`            varchar(14) NOT NULL,
  `customer_alternate_identifier`  varchar(50) NOT NULL,
  `source_system_name`             varchar(30) NOT NULL,
  `db_create_timestamp`            datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`            datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`customer_alternate_identifier`),
  KEY `fk_customer_alternate_identifier_customer_idx` (`customer_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `customer_contact` (
  `customer_identifier`           varchar(14) NOT NULL,
  `customer_contact_identifier`   varchar(14) NOT NULL,
  `title`                         varchar(50) DEFAULT NULL,
  `first_name`                    varchar(50) DEFAULT NULL,
  `last_name`                     varchar(50) DEFAULT NULL,
  `phone_number`                  varchar(20) DEFAULT NULL,
  `alternate_phone_number`        varchar(20) DEFAULT NULL,
  `email`                         varchar(50) DEFAULT NULL,
  `primary_contact_indicator`     tinyint(1)  DEFAULT NULL,
  `db_create_timestamp`           datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`           datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`customer_contact_identifier`),
  KEY `fk_customer_contact_customer_idx` (`customer_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `customer_vehicle` (
  `customer_identifier`          varchar(14) NOT NULL,
  `customer_vehicle_identifier`  varchar(14) NOT NULL,
  `vehicle_identifier`           varchar(14) NOT NULL,
  `db_create_timestamp`          datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`          datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`customer_vehicle_identifier`),
  KEY `fk_customer_contact_customer_idx` (`customer_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
