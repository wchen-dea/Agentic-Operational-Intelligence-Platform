-- ============================================================
-- 02  Site / Location / Organisation reference tables
--     region → site → site_blocking_reason, site_business_unit
--     employee, article, article_inventory, vehicle
--     agg_site_cutover_date
-- ============================================================

USE `retail_ops`;

-- ----------------------------------------------------------
-- Geographic / organisational hierarchy
-- ----------------------------------------------------------

CREATE TABLE IF NOT EXISTS `region` (
  `region_code`          varchar(6)  NOT NULL,
  `region_name`          varchar(40) DEFAULT NULL,
  `db_create_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`region_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `site_blocking_reason` (
  `blocking_reason_code`         varchar(2)  NOT NULL,
  `blocking_reason_description`  varchar(20) DEFAULT NULL,
  `db_create_timestamp`          datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`          datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`blocking_reason_code`),
  KEY `idx_sbr_brc` (`blocking_reason_code`) COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `site_business_unit` (
  `business_unit_code`   varchar(4)  NOT NULL,
  `business_unit_name`   varchar(40) DEFAULT NULL,
  `db_create_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`  datetime     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`business_unit_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `site` (
  `site_number`                    varchar(4)   NOT NULL,
  `store_code`                     varchar(10)  DEFAULT NULL,
  `site_name`                      varchar(40)  DEFAULT NULL,
  `region_code`                    varchar(6)   DEFAULT NULL,
  `site_type_code`                 varchar(10)  DEFAULT NULL,
  `regional_office_name`           varchar(35)  DEFAULT NULL,
  `site_address`                   varchar(150) DEFAULT NULL,
  `blocking_reason_code`           varchar(2)   DEFAULT NULL,
  `business_unit_code`             varchar(4)   DEFAULT NULL,
  `store_type_code`                varchar(1)   DEFAULT NULL,
  `store_general_ledger_close_date` date         DEFAULT NULL,
  `temporary_close_date`           date         DEFAULT NULL,
  `store_business_close_date`      date         DEFAULT NULL,
  `open_indicator`                 varchar(2)   DEFAULT NULL,
  `open_date`                      date         DEFAULT NULL,
  `store_sales_close_date`         date         DEFAULT NULL,
  `reopen_for_business_date`       date         DEFAULT NULL,
  `site_city_name`                 varchar(40)  DEFAULT NULL,
  `state_name`                     varchar(20)  DEFAULT NULL,
  `country_code`                   varchar(3)   DEFAULT NULL,
  `latitude`                       varchar(17)  DEFAULT NULL,
  `longitude`                      varchar(17)  DEFAULT NULL,
  `regional_warehouse_code`        varchar(10)  DEFAULT NULL,
  `cross_dock_code`                varchar(10)  DEFAULT NULL,
  `site_description`               varchar(30)  DEFAULT NULL,
  `company_code`                   varchar(4)   DEFAULT NULL,
  `internal_vendor_number`         varchar(10)  DEFAULT NULL,
  `internal_customer_number`       varchar(10)  DEFAULT NULL,
  `e3_region_code`                 varchar(5)   DEFAULT NULL,
  `site_create_date`               date         DEFAULT NULL,
  `certificate_of_occupancy_date`  date         DEFAULT NULL,
  `sales_organization_code`        varchar(4)   DEFAULT NULL,
  `purchasing_organization_number` varchar(4)   DEFAULT NULL,
  `division_code`                  varchar(2)   DEFAULT NULL,
  `local_currency_code`            varchar(5)   DEFAULT NULL,
  `tax_indicator_code`             varchar(5)   DEFAULT NULL,
  `tax_trade_in_indicator`         varchar(1)   DEFAULT NULL,
  `valuation_area_code`            varchar(4)   DEFAULT NULL,
  `eco_minutes_code`               varchar(4)   DEFAULT NULL,
  `storage_capacity_number`        varchar(30)  DEFAULT NULL,
  `logistics_calendar_code`        varchar(2)   DEFAULT NULL,
  `site_county_name`               varchar(40)  DEFAULT NULL,
  `site_state_code`                varchar(3)   DEFAULT NULL,
  `gis_postal_code`                varchar(10)  DEFAULT NULL,
  `store_group_code`               varchar(20)  DEFAULT NULL,
  `profit_center_identifier`       varchar(10)  DEFAULT NULL,
  `price_list_code`                varchar(4)   DEFAULT NULL,
  `price_list_name`                varchar(30)  DEFAULT NULL,
  `market_type`                    varchar(20)  DEFAULT NULL,
  `managed_inventory_code`         varchar(10)  DEFAULT NULL,
  `site_zip_code`                  varchar(10)  DEFAULT NULL,
  `regional_office_code`           varchar(12)  DEFAULT NULL,
  `distribution_channel_code`      varchar(2)   DEFAULT NULL,
  `business_unit_name`             varchar(30)  DEFAULT NULL,
  `blocking_reason_description`    varchar(20)  DEFAULT NULL,
  `time_zone_code`                 varchar(6)   DEFAULT NULL,
  `db_create_timestamp`            datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`            datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`site_number`),
  KEY `site_store_code_idx`  (`store_code`),
  KEY `idx_sit_brc`          (`blocking_reason_code`)   COMMENT 'ORE User defined',
  KEY `idx_sit_buc`          (`business_unit_code`)     COMMENT 'ORE User defined',
  KEY `idx_sit_cld`          (`store_sales_close_date`) COMMENT 'ORE User defined',
  KEY `idx_sit_opd`          (`open_date`)              COMMENT 'ORE User defined',
  KEY `idx_sit_rc`           (`region_code`)            COMMENT 'ORE User defined',
  KEY `idx_sit_sty`          (`store_type_code`)        COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `agg_site_cutover_date` (
  `site_number`          varchar(4) NOT NULL,
  `cutover_date`         date       NOT NULL,
  `db_create_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`site_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- Employee
-- ----------------------------------------------------------

CREATE TABLE IF NOT EXISTS `employee` (
  `employee_identifier`            varchar(30)  NOT NULL,
  `full_name`                      varchar(64)  DEFAULT NULL,
  `employee_type_name`             varchar(10)  DEFAULT NULL,
  `store_code`                     varchar(10)  DEFAULT NULL,
  `employment_status_code`         varchar(1)   DEFAULT NULL,
  `position_effective_start_date`  date         DEFAULT NULL,
  `effective_termination_date`     date         DEFAULT NULL,
  `position_name`                  varchar(100) DEFAULT NULL,
  `position_job_code`              varchar(4)   DEFAULT NULL,
  `original_hire_date`             date         DEFAULT NULL,
  `db_create_timestamp`            datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`            datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`employee_identifier`),
  KEY `idx_emp_et` (`employee_type_name`) COMMENT 'ORE User defined',
  KEY `idx_emp_fn` (`full_name`)          COMMENT 'ORE User defined',
  KEY `idx_emp_sc` (`store_code`)         COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- Article (product master)
-- ----------------------------------------------------------

CREATE TABLE IF NOT EXISTS `article` (
  `article_number`                       varchar(18)  NOT NULL,
  `article_description`                  varchar(40)  DEFAULT NULL,
  `article_type_code`                    varchar(4)   DEFAULT NULL,
  `article_upc_number`                   varchar(18)  DEFAULT NULL,
  `brand_identifier`                     varchar(4)   DEFAULT NULL,
  `brand_category_code`                  varchar(3)   DEFAULT NULL,
  `brand_description`                    varchar(60)  DEFAULT NULL,
  `family_identifier`                    varchar(5)   DEFAULT NULL,
  `family_description`                   varchar(15)  DEFAULT NULL,
  `line_identifier`                      varchar(5)   DEFAULT NULL,
  `line_description`                     varchar(20)  DEFAULT NULL,
  `vendor_identifier`                    varchar(10)  DEFAULT NULL,
  `merchandise_segment_code`             varchar(9)   DEFAULT NULL,
  `merchandise_segment_description`      varchar(50)  DEFAULT NULL,
  `external_merchandise_category_code`   varchar(18)  DEFAULT NULL,
  `store_article_size_description`       varchar(40)  DEFAULT NULL,
  `store_article_description`            varchar(40)  DEFAULT NULL,
  `core_marketing_identifier`            varchar(3)   DEFAULT NULL,
  `core_marketing_description`           varchar(40)  DEFAULT NULL,
  `base_unit_of_measure`                 varchar(3)   DEFAULT NULL,
  `created_date`                         date         DEFAULT NULL,
  `manufacturer_code`                    varchar(10)  DEFAULT NULL,
  `manufacturer_description`             varchar(100) DEFAULT NULL,
  `article_lifecycle_status_code`        varchar(2)   DEFAULT NULL,
  `article_lifecycle_description`        varchar(25)  DEFAULT NULL,
  `material_code`                        varchar(2)   DEFAULT NULL,
  `certificate_sold_indicator`           varchar(1)   DEFAULT NULL,
  `division_code`                        varchar(2)   DEFAULT NULL,
  `industry_sector_code`                 varchar(1)   DEFAULT NULL,
  `volume_unit_quantity`                 varchar(3)   DEFAULT NULL,
  `weight_unit_quantity`                 varchar(3)   DEFAULT NULL,
  `gross_weight`                         float        DEFAULT NULL,
  `net_weight`                           float        DEFAULT NULL,
  `article_deletion_flag`                tinyint(1)   DEFAULT NULL,
  `article_deletion_date`                date         DEFAULT NULL,
  `speed_rating_code`                    varchar(1)   DEFAULT NULL,
  `tire_cross_section_number`            varchar(5)   DEFAULT NULL,
  `tire_aspect_ratio`                    varchar(5)   DEFAULT NULL,
  `tire_rim_size_number`                 varchar(4)   DEFAULT NULL,
  `tire_load_range_code`                 varchar(2)   DEFAULT NULL,
  `mileage_grp_treadwell_code`           varchar(10)  DEFAULT NULL,
  `mileage_grp_treadwell_description`    varchar(100) DEFAULT NULL,
  `tire_test_grp_treadwell_code`         varchar(10)  DEFAULT NULL,
  `tire_test_grp_treadwell_description`  varchar(100) DEFAULT NULL,
  `tread_depth`                          varchar(2)   DEFAULT NULL,
  `tire_load_capacity`                   varchar(4)   DEFAULT NULL,
  `tire_load_index`                      int          DEFAULT NULL,
  `tire_diameter`                        float        DEFAULT NULL,
  `tire_construction_code`               varchar(1)   DEFAULT NULL,
  `traction_grade_code`                  varchar(2)   DEFAULT NULL,
  `treadwear_grade_code`                 varchar(3)   DEFAULT NULL,
  `side_wall_code`                       varchar(4)   DEFAULT NULL,
  `dtc_mileage_warranty`                 varchar(7)   DEFAULT NULL,
  `manufacturer_mileage_warranty`        varchar(7)   DEFAULT NULL,
  `product_rating_description`           varchar(5)   DEFAULT NULL,
  `discount_tire_max_width`              float        DEFAULT NULL,
  `discount_tire_min_width`              float        DEFAULT NULL,
  `vendor_max_width`                     float        DEFAULT NULL,
  `vendor_min_width`                     float        DEFAULT NULL,
  `temp_grade_code`                      varchar(1)   DEFAULT NULL,
  `primary_vn_load_index`                varchar(3)   DEFAULT NULL,
  `tread_design_code`                    varchar(3)   DEFAULT NULL,
  `max_air_pressure_number`              float        DEFAULT NULL,
  `wheel_width_number`                   varchar(4)   DEFAULT NULL,
  `wheel_offset_number`                  varchar(4)   DEFAULT NULL,
  `wheel_diameter_number`                varchar(4)   DEFAULT NULL,
  `wheel_style_code`                     varchar(2)   DEFAULT NULL,
  `wheel_piece_count`                    int          DEFAULT NULL,
  `wheel_bolt_pattern`                   varchar(75)  DEFAULT NULL,
  `number_of_bolts`                      int          DEFAULT NULL,
  `bolt_circle_1_size`                   float        DEFAULT NULL,
  `bolt_circle_2_size`                   float        DEFAULT NULL,
  `wheel_inner_radius_back_code`         varchar(3)   DEFAULT NULL,
  `wheel_inner_radius_code`              varchar(3)   DEFAULT NULL,
  `wheel_lip_depth`                      int          DEFAULT NULL,
  `wheel_tire_height_limit_size`         float        DEFAULT NULL,
  `wheel_color_code`                     varchar(2)   DEFAULT NULL,
  `wheel_color_description`              varchar(20)  DEFAULT NULL,
  `wheel_lug_seat_type_code`             varchar(2)   DEFAULT NULL,
  `wheel_lug_type_code`                  varchar(2)   DEFAULT NULL,
  `wheel_accent_code`                    varchar(2)   DEFAULT NULL,
  `lug_hole_diameter`                    float        DEFAULT NULL,
  `hub_clearance_size`                   int          DEFAULT NULL,
  `hub_depth_size`                       int          DEFAULT NULL,
  `hub_step_diameter`                    float        DEFAULT NULL,
  `hub_ring_type_code`                   varchar(3)   DEFAULT NULL,
  `hub_bore_size`                        float        DEFAULT NULL,
  `finish_code`                          varchar(2)   DEFAULT NULL,
  `finish_description`                   varchar(40)  DEFAULT NULL,
  `vendor_finish_code`                   varchar(40)  DEFAULT NULL,
  `volume_number`                        float        DEFAULT NULL,
  `back_spacing_size`                    float        DEFAULT NULL,
  `cavity_backed_code`                   varchar(1)   DEFAULT NULL,
  `air_sensor_indicator`                 varchar(1)   DEFAULT NULL,
  `atv_offset_number`                    varchar(9)   DEFAULT NULL,
  `mounting_pad_diameter`                varchar(3)   DEFAULT NULL,
  `mounting_pad_thickness_size`          varchar(2)   DEFAULT NULL,
  `spoke_100mm_depth`                    int          DEFAULT NULL,
  `spoke_120mm_depth`                    int          DEFAULT NULL,
  `spoke_160mm_depth`                    int          DEFAULT NULL,
  `spoke_90mm_depth`                     int          DEFAULT NULL,
  `merchandise_category_code`            varchar(40)  DEFAULT NULL,
  `merchandise_category_description`     varchar(40)  DEFAULT NULL,
  `run_flat_indicator`                   varchar(2)   DEFAULT NULL,
  `db_create_timestamp`                  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`                  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`article_number`),
  KEY `idx_art_atc`  (`article_type_code`)                   COMMENT 'ORE User defined',
  KEY `idx_art_emcc` (`external_merchandise_category_code`)  COMMENT 'ORE User defined',
  KEY `idx_art_msc`  (`merchandise_segment_code`)            COMMENT 'ORE User defined',
  KEY `idx_art_msd`  (`merchandise_segment_description`)     COMMENT 'ORE User defined',
  KEY `idx_art_prd`  (`product_rating_description`)          COMMENT 'ORE User defined',
  KEY `idx_art_sa`   (`store_article_description`)           COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `article_inventory` (
  `site_number`                   varchar(4)   NOT NULL,
  `article_number`                varchar(18)  NOT NULL,
  `reserved_quantity`             int          DEFAULT NULL,
  `on_hand_quantity`              int          DEFAULT NULL,
  `available_quantity`            int          DEFAULT NULL,
  `in_transit_quantity`           int          DEFAULT NULL,
  `layaway_quantity`              int          DEFAULT NULL,
  `weborder_quantity`             int          DEFAULT NULL,
  `purchase_decision_code`        varchar(2)   DEFAULT NULL,
  `purchase_decision_description` varchar(25)  DEFAULT NULL,
  `inventory_date`                date         NOT NULL,
  `time_offset`                   varchar(100) DEFAULT NULL,
  `db_create_timestamp`           datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`           datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`site_number`, `article_number`, `inventory_date`),
  KEY `idx_ai_id` (`inventory_date`) COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- Vehicle master
-- ----------------------------------------------------------

CREATE TABLE IF NOT EXISTS `vehicle` (
  `vehicle_identifier`              varchar(18)  NOT NULL,
  `year_number`                     varchar(4)   DEFAULT NULL,
  `make_name`                       varchar(50)  DEFAULT NULL,
  `model_name`                      varchar(50)  DEFAULT NULL,
  `vehicle_class_code`              varchar(5)   DEFAULT NULL,
  `trim_identifier`                 varchar(18)  NOT NULL,
  `assembly_identifier`             varchar(2)   NOT NULL,
  `vehicle_trim_description`        varchar(255) DEFAULT NULL,
  `front_tire_cross_section_number` float        DEFAULT NULL,
  `front_tire_aspect_ratio`         float        DEFAULT NULL,
  `front_wheel_diameter_number`     float        DEFAULT NULL,
  `vehicle_assembly_description`    varchar(35)  DEFAULT NULL,
  `deleted_indicator`               varchar(10)  DEFAULT NULL,
  `db_create_timestamp`             datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update_timestamp`             datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`vehicle_identifier`, `trim_identifier`, `assembly_identifier`),
  KEY `idx_veh_del` (`deleted_indicator`)  COMMENT 'ORE User defined',
  KEY `idx_veh_mk`  (`make_name`)          COMMENT 'ORE User defined',
  KEY `idx_veh_mod` (`model_name`)         COMMENT 'ORE User defined',
  KEY `idx_veh_vcl` (`vehicle_class_code`) COMMENT 'ORE User defined',
  KEY `idx_veh_yn`  (`year_number`)        COMMENT 'ORE User defined'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
