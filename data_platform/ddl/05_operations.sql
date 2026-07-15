-- ============================================================
-- 05  Operations tables
--     appointment → appointment_slot_reservation
--     work_order  → work_order_bay_assignment
--                   work_order_employee
--                   work_order_line_item
--     vehicle_inspection → vehicle_tire_inspection_detail
--                          vehicle_tire_inspection_measurement
-- ============================================================

USE `retail_ops`;

-- ----------------------------------------------------------
-- Appointment
-- ----------------------------------------------------------

CREATE TABLE IF NOT EXISTS `appointment` (
  `appointment_identifier`    varchar(20)  NOT NULL,
  `appointment_type_name`     varchar(40)  DEFAULT NULL,
  `sales_order_identifier`    varchar(18)  NOT NULL,
  `customer_identifier`       varchar(18)  DEFAULT NULL,
  `scheduled_start_timestamp` datetime     DEFAULT NULL,
  `actual_start_timestamp`    datetime     DEFAULT NULL,
  `status_code`               varchar(40)  DEFAULT NULL,
  `booking_origin_code`       varchar(40)  DEFAULT NULL,
  `order_type_name`           varchar(40)  DEFAULT NULL,
  `site_number`               varchar(4)   NOT NULL,
  `customer_type_name`        varchar(40)  DEFAULT NULL,
  `scheduled_duration`        double       DEFAULT NULL,
  `appointment_date`          date         DEFAULT NULL,
  `create_timestamp`          datetime     NOT NULL,
  `last_modify_timestamp`     datetime     NOT NULL,
  `time_offset`               varchar(100) DEFAULT NULL,
  `db_create_timestamp`       datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`       datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`appointment_identifier`),
  KEY `idx_app_ad`  (`appointment_date`)      COMMENT 'ORE User defined',
  KEY `idx_app_atn` (`appointment_type_name`) COMMENT 'ORE User defined',
  KEY `idx_app_cid` (`customer_identifier`)   COMMENT 'ORE User defined',
  KEY `idx_app_ctn` (`customer_type_name`)    COMMENT 'ORE User defined',
  KEY `idx_app_ctt` (`create_timestamp`)      COMMENT 'ORE User defined',
  KEY `idx_app_sc`  (`status_code`)           COMMENT 'ORE User defined',
  KEY `idx_app_sn`  (`site_number`)           COMMENT 'ORE User defined',
  KEY `idx_app_so`  (`sales_order_identifier`) COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `appointment_slot_reservation` (
  `appointment_identifier`          varchar(18) NOT NULL,
  `slot_reservation_identifier`     varchar(18) NOT NULL,
  `slot_reservation_type_code`      varchar(24) DEFAULT NULL,
  `db_create_timestamp`             datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`             datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`appointment_identifier`, `slot_reservation_identifier`),
  KEY `fk_appointment_slot_reservation_appointment_idx` (`appointment_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- Work order
-- ----------------------------------------------------------

CREATE TABLE IF NOT EXISTS `work_order` (
  `work_order_identifier`            varchar(18)  NOT NULL,
  `work_order_number`                varchar(100) NOT NULL,
  `order_type_name`                  varchar(18)  DEFAULT NULL,
  `sales_order_identifier`           varchar(18)  DEFAULT NULL,
  `appointment_identifier`           varchar(18)  DEFAULT NULL,
  `vehicle_inspection_identifier`    varchar(100) DEFAULT NULL,
  `site_number`                      varchar(4)   NOT NULL,
  `customer_identifier`              varchar(18)  DEFAULT NULL,
  `vehicle_identifier`               varchar(18)  DEFAULT NULL,
  `work_order_status`                varchar(40)  DEFAULT NULL,
  `work_order_check_in_timestamp`    datetime     DEFAULT NULL,
  `bay_in_timestamp`                 datetime     DEFAULT NULL,
  `bay_out_timestamp`                datetime     DEFAULT NULL,
  `promise_time`                     datetime     DEFAULT NULL,
  `vin`                              varchar(23)  DEFAULT NULL,
  `total_article_quantity`           double       DEFAULT NULL,
  `delay_indicator`                  tinyint(1)   DEFAULT NULL,
  `delay_reason_short`               varchar(255) DEFAULT NULL,
  `total_wait_time`                  int          DEFAULT NULL,
  `walk_in_indicator`                varchar(50)  DEFAULT NULL,
  `delay_reason_primary`             varchar(250) DEFAULT NULL,
  `delay_reason_secondary`           varchar(250) DEFAULT NULL,
  `delay_reason_tertiary`            varchar(250) DEFAULT NULL,
  `contact_first_name`               varchar(100) DEFAULT NULL,
  `contact_last_name`                varchar(100) DEFAULT NULL,
  `contact_email`                    varchar(80)  DEFAULT NULL,
  `contact_phone`                    varchar(40)  DEFAULT NULL,
  `create_timestamp`                 datetime     NOT NULL,
  `last_modify_timestamp`            datetime     NOT NULL,
  `time_offset`                      varchar(100) DEFAULT NULL,
  `work_order_type`                  varchar(30)  DEFAULT NULL,
  `db_create_timestamp`              datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`              datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`work_order_identifier`),
  KEY `idx_wo_bit`   (`bay_in_timestamp`)                COMMENT 'ORE User defined',
  KEY `idx_wo_bot`   (`bay_out_timestamp`)               COMMENT 'ORE User defined',
  KEY `idx_wo_sn`    (`site_number`)                     COMMENT 'ORE User defined',
  KEY `idx_wo_to`    (`time_offset`)                     COMMENT 'ORE User defined',
  KEY `idx_wo_wocit` (`work_order_check_in_timestamp`)   COMMENT 'ORE User defined',
  KEY `idx_wo_wot`   (`work_order_type`)                 COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `work_order_bay_assignment` (
  `work_order_identifier`  varchar(18)  NOT NULL,
  `bay_number`             varchar(100) NOT NULL,
  `bay_start_timestamp`    datetime     DEFAULT NULL,
  `bay_end_timestamp`      datetime     DEFAULT NULL,
  `bay_total_time`         int          DEFAULT NULL,
  `db_create_timestamp`    datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`    datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`work_order_identifier`, `bay_number`),
  KEY `fk_work_order_bay_assignment_work_order_idx` (`work_order_identifier`),
  KEY `idx_woba_bett` (`bay_end_timestamp`)   COMMENT 'ORE User defined',
  KEY `idx_woba_bstt` (`bay_start_timestamp`) COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `work_order_employee` (
  `work_order_identifier`   varchar(18) NOT NULL,
  `employee_identifier`     varchar(18) NOT NULL,
  `db_create_timestamp`     datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`     datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`work_order_identifier`, `employee_identifier`),
  KEY `fk_work_order_employee_work_order_idx` (`work_order_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `work_order_line_item` (
  `work_order_identifier`       varchar(18) NOT NULL,
  `line_item_number`            varchar(18) NOT NULL,
  `article_number`              varchar(18) DEFAULT NULL,
  `article_type_code`           varchar(40) DEFAULT NULL,
  `article_quantity`            double      DEFAULT NULL,
  `article_unit_price_amount`   double      DEFAULT NULL,
  `db_create_timestamp`         datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`         datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`work_order_identifier`, `line_item_number`),
  KEY `fk_work_order_line_item_work_order_idx` (`work_order_identifier`),
  KEY `idx_woli_atc` (`article_type_code`) COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- Vehicle inspection
-- ----------------------------------------------------------

CREATE TABLE IF NOT EXISTS `vehicle_inspection` (
  `inspection_identifier`             varchar(36)   NOT NULL,
  `customer_identifier`               varchar(36)   NOT NULL,
  `dot_communication_opt_in_indicator` tinyint       DEFAULT NULL,
  `vin`                               varchar(50)   DEFAULT NULL,
  `vehicle_license_plate_number`      varchar(50)   DEFAULT NULL,
  `inspection_location`               varchar(500)  DEFAULT NULL,
  `store_code`                        varchar(10)   DEFAULT NULL,
  `site_number`                       varchar(4)    NOT NULL,
  `create_worker_identifier`          varchar(50)   DEFAULT NULL,
  `create_by_source_name`             varchar(10)   NOT NULL,
  `inspection_comments`               varchar(1000) DEFAULT NULL,
  `vehicle_condition`                 varchar(1000) DEFAULT NULL,
  `mileage_reading`                   int           DEFAULT NULL,
  `kilometer_reading`                 int           DEFAULT NULL,
  `rotation_pattern`                  varchar(100)  DEFAULT NULL,
  `tpms_status`                       varchar(100)  DEFAULT NULL,
  `wheel_lock_indicator`              tinyint       DEFAULT NULL,
  `vehicle_identifier`                varchar(20)   DEFAULT NULL,
  `original_reason_code`              varchar(100)  DEFAULT NULL,
  `trim_identifier`                   varchar(18)   DEFAULT NULL,
  `assembly_identifier`               varchar(18)   DEFAULT NULL,
  `spare_in_use_indicator`            tinyint       DEFAULT NULL,
  `carry_out_indicator`               tinyint       DEFAULT NULL,
  `replace_all_tires_indicator`       tinyint       DEFAULT NULL,
  `vehicle_make`                      varchar(100)  DEFAULT NULL,
  `vehicle_model`                     varchar(50)   DEFAULT NULL,
  `replace_all_wheels_indicator`      tinyint       DEFAULT NULL,
  `vehicle_year`                      varchar(10)   DEFAULT NULL,
  `create_timestamp`                  datetime      NOT NULL,
  `last_modify_timestamp`             datetime      DEFAULT NULL,
  `time_offset`                       varchar(100)  DEFAULT NULL,
  `db_create_timestamp`               datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`               datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`inspection_identifier`),
  KEY `idx_vin_csn` (`create_by_source_name`)  COMMENT 'ORE User defined',
  KEY `idx_vin_ctt` (`create_timestamp`)        COMMENT 'ORE User defined',
  KEY `idx_vin_orc` (`original_reason_code`)    COMMENT 'ORE User defined',
  KEY `idx_vin_sc`  (`store_code`)              COMMENT 'ORE User defined',
  KEY `idx_vin_sn`  (`site_number`)             COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `vehicle_tire_inspection_detail` (
  `inspection_identifier`    varchar(36)  NOT NULL,
  `tire_position_code`       varchar(3)   NOT NULL,
  `dot_number`               varchar(100) DEFAULT NULL,
  `recall_indicator`         tinyint      DEFAULT NULL,
  `tire_services_performed`  varchar(100) DEFAULT NULL,
  `tire_age`                 double       DEFAULT NULL,
  `tire_status`              varchar(50)  DEFAULT NULL,
  `db_create_timestamp`      datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`      datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`inspection_identifier`, `tire_position_code`),
  KEY `fk_vehicle_tire_inspection_detail_vehicle_idx` (`inspection_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `vehicle_tire_inspection_measurement` (
  `inspection_identifier`   varchar(36) NOT NULL,
  `tire_position_code`      varchar(3)  NOT NULL,
  `measurement_location`    varchar(50) NOT NULL,
  `measurement_value`       float       DEFAULT NULL,
  `db_create_timestamp`     datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`     datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`inspection_identifier`, `tire_position_code`, `measurement_location`),
  KEY `fk_vehicle_tire_inspection_measurement_vehicle_idx` (`inspection_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
