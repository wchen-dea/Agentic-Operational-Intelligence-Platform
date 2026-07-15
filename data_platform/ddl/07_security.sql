-- ============================================================
-- 07  Security tables
--     agg_store_security
--     store_security
-- ============================================================

USE `retail_ops`;

CREATE TABLE IF NOT EXISTS `agg_store_security` (
  `employee_login`               varchar(30) NOT NULL,
  `region_code`                  varchar(6)  NOT NULL,
  `site_number`                  varchar(4)  NOT NULL,
  `user_login`                   varchar(50) NOT NULL,
  `blocking_reason_description`  varchar(20) DEFAULT NULL,
  `db_create_timestamp`          datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`          datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`employee_login`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `store_security` (
  `employee_login`               varchar(26) NOT NULL,
  `region_code`                  varchar(3)  NOT NULL,
  `user_login`                   varchar(26) NOT NULL,
  `blocking_reason_description`  varchar(20) DEFAULT NULL,
  `site_number`                  varchar(4)  NOT NULL,
  `db_create_timestamp`          datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`          datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`employee_login`, `site_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
