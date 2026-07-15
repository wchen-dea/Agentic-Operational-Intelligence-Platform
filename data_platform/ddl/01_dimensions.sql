-- ============================================================
-- 01  Time dimension tables
-- Grain: date → week → month → quarter → year
-- Supporting: hour, day_of_the_week, month_of_year, mtd, ytd
-- ============================================================

USE `retail_ops`;

CREATE TABLE IF NOT EXISTS `year` (
  `year_id`              int  NOT NULL,
  `previous_id`          int  DEFAULT NULL,
  `db_create_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`year_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `quarter` (
  `quarter_id`            int          NOT NULL,
  `quarter_desc`          varchar(16)  NOT NULL,
  `quarter_of_year_id`    int          NOT NULL,
  `year_id`               int          NOT NULL,
  `previous_quarter_id`   int          NOT NULL,
  `last_year_quarter_id`  int          NOT NULL,
  `quarter_duration`      int          NOT NULL,
  `db_create_timestamp`   datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`   datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`quarter_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `month_of_year` (
  `month_of_year_id`           int         NOT NULL,
  `month_of_year_desc`         varchar(32) DEFAULT NULL,
  `month_of_year_short_desc`   varchar(32) DEFAULT NULL,
  `previous_month_of_year_id`  int         DEFAULT NULL,
  `db_create_timestamp`        datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`        datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`month_of_year_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `month` (
  `month_id`                 int         NOT NULL,
  `month_desc`               varchar(32) DEFAULT NULL,
  `month_of_year_id`         int         DEFAULT NULL,
  `previous_month_id`        int         DEFAULT NULL,
  `previous_year_month_id`   int         DEFAULT NULL,
  `month_duration`           int         DEFAULT NULL,
  `quarter_id`               int         DEFAULT NULL,
  `db_create_timestamp`      datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`      datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`month_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `week` (
  `week_id`              int         NOT NULL,
  `month_id`             int         NOT NULL,
  `year_id`              int         NOT NULL,
  `week_desc`            varchar(16) DEFAULT NULL,
  `week_begin_date`      date        NOT NULL,
  `week_end_date`        date        NOT NULL,
  `week_range`           varchar(50) NOT NULL,
  `previous_week_id`     int         NOT NULL,
  `db_create_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`week_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `day_of_the_week` (
  `day_of_week_id`        int         NOT NULL,
  `day_of_week_desc`      varchar(32) DEFAULT NULL,
  `day_of_week_short_desc` varchar(4) DEFAULT NULL,
  `part_of_week_id`       int         DEFAULT NULL,
  `db_create_timestamp`   datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`   datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`day_of_week_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `date` (
  `date_id`                      date        NOT NULL,
  `week_id`                      int         NOT NULL,
  `month_id`                     int         NOT NULL,
  `quarter_id`                   int         NOT NULL,
  `year_id`                      int         NOT NULL,
  `day_of_week_id`               int         NOT NULL,
  `month_of_year_id`             int         NOT NULL,
  `day_over_day_date_id`         date        NOT NULL,
  `calendar_compare_date_id`     date        NOT NULL,
  `previous_quarter_month_id`    int         NOT NULL,
  `work_day_indicator`           varchar(1)  NOT NULL,
  `db_create_timestamp`          datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`          datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`date_id`),
  KEY `idx_dat_ccd` (`calendar_compare_date_id`) COMMENT 'ORE User defined',
  KEY `idx_dat_dod` (`day_over_day_date_id`)     COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `hour` (
  `hour_id`              int        NOT NULL,
  `hour_desc`            varchar(4) DEFAULT NULL,
  `db_create_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`hour_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `mtd` (
  `date_id`              date        NOT NULL,
  `month_to_date_id`     varchar(4)  DEFAULT NULL,
  `db_create_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`date_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `ytd` (
  `date_id`              date       NOT NULL,
  `year_to_date_id`      varchar(4) DEFAULT NULL,
  `db_create_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`date_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
