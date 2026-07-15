-- ============================================================
-- 04  Sales order and receipt tables
--
--  sales_order
--    └── sales_order_line_item
--          ├── sales_order_line_item_fee
--          ├── sales_order_line_item_promotion
--          └── sales_order_line_item_tax
--    └── sales_order_promotion
--    └── sales_order_treadwell_session
--
--  sales_order_receipt
--    └── sales_order_receipt_line_item
--          ├── sales_order_receipt_line_item_allocation
--          ├── sales_order_receipt_line_item_fee
--          ├── sales_order_receipt_line_item_promotion
--          └── sales_order_receipt_line_item_tax
--    └── sales_order_receipt_payment
--    └── sales_order_receipt_promotion
--
--  voucher
-- ============================================================

USE `retail_ops`;

-- ----------------------------------------------------------
-- Sales order header
-- ----------------------------------------------------------

CREATE TABLE IF NOT EXISTS `sales_order` (
  `sales_order_identifier`                varchar(10)  NOT NULL,
  `site_number`                           varchar(4)   DEFAULT NULL,
  `customer_identifier`                   varchar(14)  DEFAULT NULL,
  `create_employee_identifier`            varchar(30)  DEFAULT NULL,
  `processor_employee_identifier`         varchar(30)  DEFAULT NULL,
  `customer_vehicle_identifier`           varchar(40)  DEFAULT NULL,
  `vehicle_identifier`                    varchar(18)  DEFAULT NULL,
  `trim_identifier`                       varchar(18)  DEFAULT NULL,
  `assembly_identifier`                   varchar(2)   DEFAULT NULL,
  `sales_order_created_date`              date         DEFAULT NULL,
  `sales_order_status_code`               varchar(1)   DEFAULT NULL,
  `sales_order_status_description`        varchar(20)  DEFAULT NULL,
  `sales_order_document_type_code`        varchar(4)   DEFAULT NULL,
  `sales_order_document_type_description` varchar(20)  DEFAULT NULL,
  `order_transaction_type_code`           varchar(2)   DEFAULT NULL,
  `order_transaction_type_description`    varchar(35)  DEFAULT NULL,
  `time_offset`                           varchar(6)   DEFAULT NULL,
  `pos_event_code`                        varchar(2)   DEFAULT NULL,
  `pos_event_description`                 varchar(35)  DEFAULT NULL,
  `sales_order_origin_code`               varchar(35)  DEFAULT NULL,
  `tax_exempt_certificate_number`         varchar(20)  DEFAULT NULL,
  `sales_order_reason_code`               varchar(20)  DEFAULT NULL,
  `sales_order_reason_description`        varchar(20)  DEFAULT NULL,
  `lift_identifier`                       varchar(4)   DEFAULT NULL,
  `return_type_code`                      varchar(1)   DEFAULT NULL,
  `reference_sales_order_identifier`      varchar(10)  DEFAULT NULL,
  `quote_indicator`                       varchar(10)  DEFAULT NULL,
  `datasphere_timestamp_vbak`             datetime     DEFAULT NULL,
  `datasphere_timestamp_vbap`             datetime     DEFAULT NULL,
  `datasphere_timestamp_vbfa`             datetime     DEFAULT NULL,
  `datasphere_timestamp_vbuk`             datetime     DEFAULT NULL,
  `datasphere_timestamp_vbrp`             datetime     DEFAULT NULL,
  `sap_row_creation_timestamp_vbak`       datetime     DEFAULT NULL,
  `sap_row_creation_timestamp_vbap`       datetime     DEFAULT NULL,
  `sap_row_creation_timestamp_vbfa`       datetime     DEFAULT NULL,
  `sap_row_creation_timestamp_vbrp`       datetime     DEFAULT NULL,
  `kafka_event_time`                      datetime     DEFAULT NULL,
  `flink_proc_time`                       datetime     DEFAULT NULL,
  `last_modify_timestamp`                 varchar(19)  DEFAULT NULL,
  `db_create_timestamp`                   datetime     DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`                   datetime     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_identifier`),
  KEY `idx_so_cd`   (`sales_order_created_date`)           COMMENT 'ORE User defined',
  KEY `idx_so_cid`  (`customer_identifier`)                COMMENT 'ORE User defined',
  KEY `idx_so_ltt`  (`last_modify_timestamp`)              COMMENT 'ORE User defined',
  KEY `idx_so_sc`   (`sales_order_status_code`)            COMMENT 'ORE User defined',
  KEY `idx_so_sn`   (`site_number`)                        COMMENT 'ORE User defined',
  KEY `idx_so_tc`   (`order_transaction_type_code`)        COMMENT 'ORE User defined',
  KEY `idx_so_vid`  (`vehicle_identifier`)                 COMMENT 'ORE User defined',
  KEY `idx_so_stc`  (`return_type_code`)                   COMMENT 'ore user defined',
  KEY `idx_so_rsoi` (`reference_sales_order_identifier`)   COMMENT 'ore user defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_line_item` (
  `sales_order_identifier`                    varchar(10)  NOT NULL,
  `sales_order_line_item_number`              int          NOT NULL,
  `sales_order_line_item_status_code`         varchar(1)   DEFAULT NULL,
  `sales_order_line_item_status_description`  varchar(100) DEFAULT NULL,
  `article_number`                            varchar(18)  NOT NULL,
  `sales_order_line_item_created_date`        datetime     DEFAULT NULL,
  `sold_quantity`                             float        DEFAULT NULL,
  `retail_price`                              float        DEFAULT NULL,
  `discount_amount`                           float        DEFAULT NULL,
  `net_price`                                 float        DEFAULT NULL,
  `manager_deviation_amount`                  float        DEFAULT NULL,
  `adjustment_type_code`                      varchar(3)   DEFAULT NULL,
  `adjustment_type_description`               varchar(40)  DEFAULT NULL,
  `return_reason_code`                        varchar(10)  DEFAULT NULL,
  `line_item_cancellation_code`               varchar(2)   DEFAULT NULL,
  `line_item_cancellation_description`        varchar(40)  DEFAULT NULL,
  `misc_article_size_description`             varchar(40)  DEFAULT NULL,
  `adjustment_article_install_mileage`        varchar(20)  DEFAULT NULL,
  `parent_line_item_number`                   varchar(20)  DEFAULT NULL,
  `sales_order_line_item_type_code`           varchar(4)   DEFAULT NULL,
  `sales_order_line_item_type_description`    varchar(20)  DEFAULT NULL,
  `price_reason_description`                  varchar(25)  DEFAULT NULL,
  `certificate_redeemed_quantity`             float        DEFAULT NULL,
  `mvi_article_indicator`                     tinyint(1)   DEFAULT NULL,
  `vehicle_generic_category`                  varchar(50)  DEFAULT NULL,
  `vehicle_generic_sub_category`              varchar(50)  DEFAULT NULL,
  `order_reason_code`                         varchar(4)   DEFAULT NULL,
  `order_reason_description`                  varchar(50)  DEFAULT NULL,
  `db_create_timestamp`                       datetime     DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`                       datetime     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_identifier`, `sales_order_line_item_number`),
  KEY `fk_sales_order_line_item_sales_order_idx` (`sales_order_identifier`),
  KEY `idx_sol_art` (`article_number`)                        COMMENT 'ORE User defined',
  KEY `idx_sol_sc`  (`sales_order_line_item_status_code`)     COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_line_item_fee` (
  `sales_order_identifier`          varchar(10) NOT NULL,
  `sales_order_line_item_number`    int         NOT NULL,
  `line_item_fee_type_code`         varchar(4)  NOT NULL,
  `line_item_fee_type_description`  varchar(20) DEFAULT NULL,
  `line_item_fee_amount`            float       DEFAULT NULL,
  `db_create_timestamp`             datetime    DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`             datetime    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_identifier`, `sales_order_line_item_number`, `line_item_fee_type_code`),
  KEY `fk_sales_order_line_item_fee_sales_order_idx` (`sales_order_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_line_item_promotion` (
  `sales_order_identifier`               varchar(10)  NOT NULL,
  `sales_order_line_item_number`         int          NOT NULL,
  `line_item_promotion_type_code`        varchar(10)  NOT NULL,
  `line_item_promotion_type_description` varchar(100) DEFAULT NULL,
  `line_item_promotion_amount`           float        DEFAULT NULL,
  `line_item_promotion_article_number`   varchar(18)  DEFAULT NULL,
  `db_create_timestamp`                  datetime     DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`                  datetime     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_identifier`, `sales_order_line_item_number`, `line_item_promotion_type_code`),
  KEY `fk_sales_order_line_item_promotion_sales_order_idx` (`sales_order_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_line_item_tax` (
  `sales_order_identifier`          varchar(10) NOT NULL,
  `sales_order_line_item_number`    int         NOT NULL,
  `line_item_tax_type_code`         varchar(4)  NOT NULL,
  `line_item_tax_type_description`  varchar(20) DEFAULT NULL,
  `line_item_tax_amount`            float       DEFAULT NULL,
  `db_create_timestamp`             datetime    DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`             datetime    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_identifier`, `sales_order_line_item_number`, `line_item_tax_type_code`),
  KEY `fk_sales_order_line_item_tax_sales_order_idx` (`sales_order_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_promotion` (
  `sales_order_identifier`               varchar(10)  NOT NULL,
  `header_promotion_type_code`           varchar(4)   NOT NULL,
  `sales_order_line_item_number`         int          NOT NULL,
  `header_promotion_type_description`    varchar(100) DEFAULT NULL,
  `header_promotion_amount`              float        DEFAULT NULL,
  `header_promotion_article_number`      varchar(18)  DEFAULT NULL,
  `db_create_timestamp`                  datetime     DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`                  datetime     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_identifier`, `header_promotion_type_code`, `sales_order_line_item_number`),
  KEY `fk_sales_order_promotion_sales_order_idx` (`sales_order_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_treadwell_session` (
  `record_identifier`              varchar(25) NOT NULL,
  `sales_order_identifier`         varchar(15) NOT NULL,
  `sales_order_line_item_number`   int         DEFAULT NULL,
  `treadwell_session_identifier`   varchar(50) DEFAULT NULL,
  `db_create_timestamp`            datetime    DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`            datetime    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`record_identifier`),
  KEY `idx_sots_id`   (`sales_order_identifier`)       COMMENT 'ORE User defined',
  KEY `idx_sots_li`   (`sales_order_line_item_number`) COMMENT 'ORE User defined',
  KEY `idx_sots_twid` (`treadwell_session_identifier`) COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- Sales order receipt header
-- ----------------------------------------------------------

CREATE TABLE IF NOT EXISTS `sales_order_receipt` (
  `sales_order_receipt_identifier`                    varchar(10) NOT NULL,
  `sales_order_identifier`                            varchar(10) DEFAULT NULL,
  `sales_order_receipt_document_type_code`            varchar(4)  DEFAULT NULL,
  `sales_order_receipt_document_type_description`     varchar(20) DEFAULT NULL,
  `sales_order_receipt_posting_date`                  date        DEFAULT NULL,
  `site_number`                                       varchar(4)  DEFAULT NULL,
  `customer_identifier`                               varchar(14) DEFAULT NULL,
  `customer_vehicle_identifier`                       varchar(40) DEFAULT NULL,
  `vehicle_identifier`                                varchar(18) DEFAULT NULL,
  `trim_identifier`                                   varchar(18) DEFAULT NULL,
  `assembly_identifier`                               varchar(2)  DEFAULT NULL,
  `sales_order_receipt_transaction_type_code`         varchar(2)  DEFAULT NULL,
  `sales_order_receipt_transaction_type_description`  varchar(35) DEFAULT NULL,
  `last_modify_timestamp`                             varchar(19) DEFAULT NULL,
  `sales_order_receipt_created_date`                  date        DEFAULT NULL,
  `quote_indicator`                                   varchar(1)  DEFAULT NULL,
  `carryout_indicator`                                varchar(1)  DEFAULT NULL,
  `hybris_customer_number`                            varchar(40) DEFAULT NULL,
  `time_offset`                                       varchar(6)  DEFAULT NULL,
  `return_type_code`                                  varchar(1)  DEFAULT NULL,
  `reference_sales_order_identifier`                  varchar(10) DEFAULT NULL,
  `datasphere_timestamp_vbrk`                         datetime    DEFAULT NULL,
  `datasphere_timestamp_vbrp`                         datetime    DEFAULT NULL,
  `datasphere_timestamp_vbak`                         datetime    DEFAULT NULL,
  `datasphere_timestamp_vbap`                         datetime    DEFAULT NULL,
  `sap_row_creation_timestamp_vbrk`                   datetime    DEFAULT NULL,
  `sap_row_creation_timestamp_vbrp`                   datetime    DEFAULT NULL,
  `sap_row_creation_timestamp_vbak`                   datetime    DEFAULT NULL,
  `sap_row_creation_timestamp_vbap`                   datetime    DEFAULT NULL,
  `kafka_event_time`                                  datetime    DEFAULT NULL,
  `flink_proc_time`                                   datetime    DEFAULT NULL,
  `db_create_timestamp`                               datetime    DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`                               datetime    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_receipt_identifier`),
  KEY `idx_sor_cd`   (`sales_order_receipt_created_date`)             COMMENT 'ORE User defined',
  KEY `idx_sor_cid`  (`customer_identifier`)                          COMMENT 'ORE User defined',
  KEY `idx_sor_dtc`  (`sales_order_receipt_document_type_code`)       COMMENT 'ORE User defined',
  KEY `idx_sor_pd`   (`sales_order_receipt_posting_date`)             COMMENT 'ORE User defined',
  KEY `idx_sor_sn`   (`site_number`)                                  COMMENT 'ORE User defined',
  KEY `idx_sor_soi`  (`sales_order_identifier`)                       COMMENT 'ORE User defined',
  KEY `idx_sor_tty`  (`sales_order_receipt_transaction_type_code`)    COMMENT 'ORE User defined',
  KEY `idx_sor_vid`  (`vehicle_identifier`)                           COMMENT 'ORE User defined',
  KEY `idx_sor_rtc`  (`return_type_code`)                             COMMENT 'ore user defined',
  KEY `idx_sor_rsoi` (`reference_sales_order_identifier`)             COMMENT 'ore user defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_receipt_line_item` (
  `sales_order_receipt_identifier`                varchar(10) NOT NULL,
  `sales_order_receipt_line_item_number`          int         NOT NULL,
  `certificate_redeemed_indicator`                tinyint(1)  DEFAULT NULL,
  `sales_order_line_item_number`                  int         DEFAULT NULL,
  `sales_order_receipt_line_item_type_code`       varchar(4)  DEFAULT NULL,
  `sales_order_receipt_line_item_type_description` varchar(20) DEFAULT NULL,
  `article_number`                                varchar(18) NOT NULL,
  `sold_quantity`                                 float       DEFAULT NULL,
  `retail_price`                                  float       DEFAULT NULL,
  `discount_amount`                               float       DEFAULT NULL,
  `net_price`                                     float       DEFAULT NULL,
  `manager_deviation_amount`                      float       DEFAULT NULL,
  `mvi_article_indicator`                         tinyint     DEFAULT NULL,
  `dot_number`                                    varchar(13) DEFAULT NULL,
  `adjustment_type_code`                          varchar(3)  DEFAULT NULL,
  `adjustment_type_description`                   varchar(40) DEFAULT NULL,
  `adjustment_article_current_mileage`            int         DEFAULT NULL,
  `adjustment_article_tread_depth`                int         DEFAULT NULL,
  `extended_cost`                                 float       DEFAULT NULL,
  `article_install_mileage`                       int         DEFAULT NULL,
  `sales_order_receipt_parent_line_number`        int         DEFAULT NULL,
  `item_gl_charge_code`                           varchar(20) DEFAULT NULL,
  `order_reason_code`                             varchar(4)  DEFAULT NULL,
  `order_reason_description`                      varchar(50) DEFAULT NULL,
  `price_reason_description`                      varchar(25) DEFAULT NULL,
  `return_reason_code`                            varchar(10) DEFAULT NULL,
  `db_create_timestamp`                           datetime    DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`                           datetime    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_receipt_identifier`, `sales_order_receipt_line_item_number`),
  KEY `fk_sales_order_receipt_line_item_sales_order_receipt_idx` (`sales_order_receipt_identifier`),
  KEY `idx_sorl_an`  (`article_number`)                                COMMENT 'ORE User defined',
  KEY `idx_sorl_aty` (`adjustment_type_code`)                          COMMENT 'ORE User defined',
  KEY `idx_sorl_cri` (`certificate_redeemed_indicator`)                COMMENT 'ORE User defined',
  KEY `idx_sorl_lty` (`sales_order_receipt_line_item_type_code`)       COMMENT 'ORE User defined',
  KEY `idx_sor_orc`  (`order_reason_code`)                             COMMENT 'ore user defined',
  KEY `idx_sor_rrc`  (`return_reason_code`)                            COMMENT 'ore user defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_receipt_line_item_allocation` (
  `sales_order_receipt_identifier`         varchar(10) NOT NULL,
  `sales_order_receipt_line_item_number`   int         NOT NULL,
  `pricing_condition_code`                 varchar(6)  NOT NULL,
  `general_ledger_account_number`          varchar(10) DEFAULT NULL,
  `allocation_amount`                      float       DEFAULT NULL,
  `db_create_timestamp`                    datetime    DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`                    datetime    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_receipt_identifier`, `sales_order_receipt_line_item_number`, `pricing_condition_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_receipt_line_item_fee` (
  `sales_order_receipt_identifier`         varchar(10) NOT NULL,
  `sales_order_receipt_line_item_number`   int         NOT NULL,
  `line_item_fee_type_code`                varchar(4)  NOT NULL,
  `line_item_fee_type_description`         varchar(20) DEFAULT NULL,
  `line_item_fee_amount`                   float       DEFAULT NULL,
  `db_create_timestamp`                    datetime    DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`                    datetime    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_receipt_identifier`, `sales_order_receipt_line_item_number`, `line_item_fee_type_code`),
  KEY `fk_sales_order_receipt_line_item_fee_sales_order_receipt_idx` (`sales_order_receipt_identifier`),
  KEY `idx_sorf_fty` (`line_item_fee_type_code`) COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_receipt_line_item_promotion` (
  `sales_order_receipt_identifier`         varchar(10)  NOT NULL,
  `sales_order_receipt_line_item_number`   int          NOT NULL,
  `line_item_promotion_type_code`          varchar(20)  NOT NULL,
  `line_item_promotion_type_description`   varchar(100) DEFAULT NULL,
  `line_item_promotion_amount`             float        DEFAULT NULL,
  `line_item_promotion_article_number`     varchar(18)  DEFAULT NULL,
  `db_create_timestamp`                    datetime     DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`                    datetime     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_receipt_identifier`, `sales_order_receipt_line_item_number`, `line_item_promotion_type_code`),
  KEY `fk_sales_order_receipt_line_item_promotion_sales_order_receipt` (`sales_order_receipt_identifier`),
  KEY `idx_sorp_prot` (`line_item_promotion_type_code`) COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_receipt_line_item_tax` (
  `sales_order_receipt_identifier`         varchar(10) NOT NULL,
  `sales_order_receipt_line_item_number`   int         NOT NULL,
  `line_item_tax_type_code`                varchar(4)  NOT NULL,
  `line_item_tax_type_description`         varchar(20) DEFAULT NULL,
  `line_item_tax_amount`                   float       DEFAULT NULL,
  `db_create_timestamp`                    datetime    DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`                    datetime    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_receipt_identifier`, `sales_order_receipt_line_item_number`, `line_item_tax_type_code`),
  KEY `fk_sales_order_receipt_line_item_tax_sales_order_receipt_idx` (`sales_order_receipt_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_receipt_payment` (
  `sales_order_receipt_identifier`           varchar(10) NOT NULL,
  `payment_id`                               int         NOT NULL,
  `sales_order_receipt_payment_type_code`    varchar(4)  DEFAULT NULL,
  `payment_type_description`                 varchar(20) DEFAULT NULL,
  `payment_amount`                           float       DEFAULT NULL,
  `db_create_timestamp`                      datetime    DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`                      datetime    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_receipt_identifier`, `payment_id`),
  KEY `idx_sorp_payt` (`sales_order_receipt_payment_type_code`) COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_receipt_promotion` (
  `sales_order_receipt_identifier`              varchar(10)  NOT NULL,
  `header_promotion_type_code`                  varchar(20)  NOT NULL,
  `sales_order_line_item_promotion_number`      int          NOT NULL,
  `header_promotion_type_description`           varchar(100) DEFAULT NULL,
  `header_promotion_amount`                     float        DEFAULT NULL,
  `header_promotion_article_number`             varchar(18)  DEFAULT NULL,
  `db_create_timestamp`                         datetime     DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`                         datetime     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`sales_order_receipt_identifier`, `header_promotion_type_code`, `sales_order_line_item_promotion_number`),
  KEY `fk_sales_order_receipt_promotion_sales_order_receipt_idx` (`sales_order_receipt_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- Voucher
-- ----------------------------------------------------------

CREATE TABLE IF NOT EXISTS `voucher` (
  `voucher_number`                    varchar(100) NOT NULL,
  `site_number`                       varchar(10)  NOT NULL,
  `voucher_type`                      varchar(100) NOT NULL,
  `voucher_posted_date`               date         NOT NULL,
  `voucher_type_description`          varchar(100) DEFAULT NULL,
  `voucher_bag_id`                    varchar(100) DEFAULT NULL,
  `voucher_amount`                    float        NOT NULL,
  `employee_identifier`               varchar(30)  DEFAULT NULL,
  `voucher_category_code`             varchar(4)   DEFAULT NULL,
  `voucher_category_description`      varchar(100) DEFAULT NULL,
  `voucher_comments`                  varchar(255) DEFAULT NULL,
  `row_key`                           int          NOT NULL,
  `financial_transaction_item_number` varchar(10)  NOT NULL,
  `db_create_timestamp`               datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`               datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`voucher_number`, `site_number`, `voucher_posted_date`, `voucher_type`, `row_key`, `financial_transaction_item_number`),
  KEY `idx_vou_sn`  (`site_number`)            COMMENT 'ORE User defined',
  KEY `idx_vou_vbi` (`voucher_bag_id`)         COMMENT 'ORE User defined',
  KEY `idx_vou_vca` (`voucher_category_code`)  COMMENT 'ORE User defined',
  KEY `idx_vou_vpd` (`voucher_posted_date`)    COMMENT 'ORE User defined',
  KEY `idx_vou_vt`  (`voucher_type`)           COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
