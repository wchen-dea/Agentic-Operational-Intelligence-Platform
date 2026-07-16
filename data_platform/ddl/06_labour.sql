-- ============================================================
-- 06  Labour / scheduling tables
--     kronos_hours
--     reflexis_weekly_staff_metrics
-- ============================================================

USE `retail_ops`;

CREATE TABLE IF NOT EXISTS `kronos_hours` (
  `person_number`             varchar(15) NOT NULL,
  `adjusted_apply_date`       date        DEFAULT NULL,
  `pay_code_name`             varchar(50) NOT NULL,
  `pay_code_type`             varchar(1)  NOT NULL,
  `person_full_name`          varchar(64) DEFAULT NULL,
  `start_timestamp_local`     varchar(19) NOT NULL,
  `end_timestamp_local`       varchar(19) DEFAULT NULL,
  `time_sheet_item_identifier` int        NOT NULL,
  `time_in_seconds`           varchar(9)  DEFAULT NULL,
  `part_time_indicator`       tinyint(1)  DEFAULT NULL,
  `store_code`                varchar(10) DEFAULT NULL,
  `time_offset`               varchar(100) DEFAULT NULL,
  `db_create_timestamp`       datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`       datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`time_sheet_item_identifier`, `pay_code_name`, `start_timestamp_local`),
  KEY `idx_kh_aad` (`adjusted_apply_date`)  COMMENT 'ORE User defined',
  KEY `idx_kh_pn`  (`person_number`)        COMMENT 'ORE User defined',
  KEY `idx_kh_pti` (`part_time_indicator`)  COMMENT 'ORE User defined',
  KEY `idx_kh_sc`  (`store_code`)           COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `reflexis_weekly_staff_metrics` (
  `site_number`                      varchar(4)  NOT NULL,
  `system_store_identifier`          int         NOT NULL,
  `system_department_identifier`     int         NOT NULL,
  `staff_group`                      varchar(16) NOT NULL,
  `week_indicator`                   int         DEFAULT NULL,
  `system_date_identifier`           int         NOT NULL,
  `create_timestamp`                 datetime    NOT NULL,
  `last_modify_timestamp`            datetime    NOT NULL,
  `demand_hours`                     float       DEFAULT NULL,
  `system_gross_scheduled_hours`     float       DEFAULT NULL,
  `system_scheduled_hours`           float       DEFAULT NULL,
  `week_scheduled_hours`             float       DEFAULT NULL,
  `manager_gross_scheduled_hours`    float       DEFAULT NULL,
  `manager_scheduled_hours`          float       DEFAULT NULL,
  `db_create_timestamp`              datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`              datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`site_number`, `system_store_identifier`, `system_department_identifier`,
               `staff_group`, `system_date_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
