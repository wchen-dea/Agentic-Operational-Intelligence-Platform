# Data Platform Architecture

Eight-stage pipeline that transforms raw source-system events into a queryable Iceberg lakehouse and downstream analytics/ML layer.

## Pipeline stages

| # | Stage | Input | Output | Code |
|---|-------|-------|--------|------|
| 1 | **Ingestion** | Aurora MySQL / synthetic data | 15 canonical Avro Kafka topics (`Canonical*`) | `data_platform/producer/` `data_platform/schema/` |
| 2 | **Flink Stream Processing** | `Canonical*` Kafka topics | PDM Sink Kafka topics (`Sink*`) | `data_platform/flink_job/` Flink :8082 |
| 3 | **Kafka Connect JDBC Sink** | `Sink*` Kafka topics | MySQL ODS `retail_ops` | `container/scripts/register_connectors.py` |
| 4 | **Debezium CDC** | MySQL ODS binlog | `retail_ops.aurora.*` CDC topics | `container/scripts/register_cdc_connector.py` |
| 5 | **Spark Streaming → Landing** | CDC Kafka topics | `iceberg.landing.*` (append) | `data_platform/spark/cdc_to_landing.py` |
| 6 | **dbt Lakehouse** | `iceberg.landing.*` | `iceberg.bronze/silver/gold/analytics` | `data_platform/dbt/` Airflow :8085 |
| 7 | **Analytics / ML / LLM** | `iceberg.gold/analytics` | Feature store, vector index, semantic layer | `data_platform/feature_store/` `data_platform/vector_index/` |

> The AI Systems (real-time path) runs in parallel from the MySQL ODS — see [architecture_ai_systems.md](architecture_ai_systems.md).

## Component diagram

```mermaid
graph TB
    subgraph Stage1["Stage 1 · Ingestion"]
        AURORA["Source Systems\nAurora MySQL / Synthetic Producer\ndata_platform/producer/"]
        SR["Schema Registry :8081\nAvro schemas — data_platform/schema/"]
    end

    subgraph Stage2["Stage 2 · Flink Stream Processing :8082"]
        FLINK["14 PyFlink Table API Jobs\ndata_platform/flink_job/\nCanonical* → Sink* topics"]
    end

    subgraph Stage3["Stage 3 · Kafka Connect JDBC Sink :8083"]
        KC["JDBC Sink Connectors\ncontainer/scripts/register_connectors.py"]
        MYSQL["MySQL ODS :3306\nretail_ops"]
    end

    subgraph Stage4["Stage 4 · Debezium CDC"]
        DBZ["Debezium Source Connector\ncontainer/scripts/register_cdc_connector.py\nMySQL binlog → retail_ops.aurora.*"]
    end

    subgraph Stage5["Stage 5 · Spark Streaming → MinIO Landing"]
        SPARK["Spark Structured Streaming\ndata_platform/spark/cdc_to_landing.py"]
        MINIO["MinIO :9000\nIceberg REST Catalog :8181\niceberg.landing.* (append-only)"]
    end

    subgraph Stage6["Stage 6 · dbt Lakehouse (Airflow :8085)"]
        STG["models/staging\nViews over landing tables"]
        BRZ["models/bronze\nCDC flatten + append"]
        SLV["models/silver\nCDC MERGE + hard DELETE"]
        GLD["models/gold\ngold_store_kpis"]
        ANL["models/analytics\nfeat_store_performance\nfeat_customer_behavior"]
    end

    subgraph Stage7["Stage 7 · Analytics / ML / LLM"]
        FEAST["Feast Feature Store :6566\nOffline: Iceberg  Online: Redis\ndata_platform/feature_store/"]
        QDRANT["Qdrant :6333\nstore_kpi_narratives\nmetric_definitions\ndata_platform/vector_index/"]
        SEMLAY["MetricFlow Semantic Layer\n9 named metrics\ndata_platform/dbt/models/semantic/"]
    end

    KAFKA["Kafka :9092–9094\nKRaft 3-broker"]

    AURORA -->|"15 canonical Avro topics"| KAFKA
    KAFKA <--> SR
    KAFKA -->|"Canonical*"| FLINK -->|"Sink* topics"| KAFKA
    KAFKA -->|"Sink* topics"| KC --> MYSQL
    MYSQL -->|"binlog"| DBZ -->|"retail_ops.aurora.*"| KAFKA
    KAFKA -->|"CDC topics"| SPARK --> MINIO
    MINIO --> STG --> BRZ --> SLV --> GLD --> ANL
    GLD --> FEAST
    ANL --> FEAST
    GLD --> QDRANT
    GLD --> SEMLAY
```

## Stage details

### Stage 1 — Ingestion

Publishes Avro-encoded events to 15 canonical Kafka topics, simulating or relaying Aurora MySQL operational transactions.

**Canonical topics produced:**

| Domain | Kafka topic |
|--------|------------|
| Salesforce CRM | `CanonicalSalesforceCrmAppointment`, `CanonicalSalesforceCrmCustomer` |
| SAP Sales Orders | `CanonicalSapSalesorderDetail`, `CanonicalSapSalesorderHybris`, `CanonicalSapSalesorderInvoice`, `CanonicalSapSalesorderVouche` |
| Trendwell Vehicles | `CanonicalTrendwellVehivleInspection`, `CanonicalTrendwellVehivleMaster`, `CanonicalTrendwellVehivleWorkorder` |
| Kronos Workforce | `CanonicalKronosCrewtime`, `CanonicalKronosEmployee`, `CanonicalKronosHours`, `CanonicalKronosSite` |
| Warehouse Inventory | `CanonicalWarehouseInventoryProduct`, `CanonicalWarehouseInventorySnapshot` |

Avro schemas: `data_platform/schema/*.avsc` · registered in Schema Registry at startup.

### Stage 2 — Flink Stream Processing

14 stateless PyFlink Table API jobs, one per business domain. Each job:
- Sources from a canonical Avro topic (Schema Registry deserialization)
- Applies field mapping, type casting, and domain logic
- Sinks to one or more PDM `Sink*` Kafka topics

| Pipeline | Canonical source | Sink topics |
|----------|-----------------|-------------|
| appointment | `CanonicalSalesforceCrmAppointment` | `SinkAppointment`, `SinkAppointmentSlotReservation` |
| customer | `CanonicalSalesforceCrmCustomer` | `SinkCustomer`, `SinkCustomerContact`, `SinkCustomerAlternateIdentifier`, `SinkCustomerVehicle` |
| sales_order | `CanonicalSapSalesorderDetail` | `SinkSalesOrder`, `SinkSalesOrderLineItem`, `SinkSalesOrderLineItemFee`, `SinkSalesOrderLineItemTax`, `SinkSalesOrderLineItemPromotion`, `SinkSalesOrderPromotion` |
| sales_order_receipt | `CanonicalSapSalesorderInvoice` | `SinkSalesOrderReceipt` + 6 child tables |
| voucher | `CanonicalSapSalesorderVouche` | `SinkVoucher` |
| vehicle_inspection | `CanonicalTrendwellVehivleInspection` | `SinkVehicleInspection`, tire detail/measurement |
| vehicle | `CanonicalTrendwellVehivleMaster` | `SinkVehicle` |
| work_order | `CanonicalTrendwellVehivleWorkorder` | `SinkWorkOrder` + line items, bay assignment, employee |
| article | `CanonicalWarehouseInventoryProduct` | `SinkArticle` |
| inventory | `CanonicalWarehouseInventorySnapshot` | `SinkArticleInventory` |
| crewtime | `CanonicalKronosCrewtime` | `SinkReflexisWeeklyStaffMetrics` |
| employee | `CanonicalKronosEmployee` | `SinkEmployee` |
| kronos_hours | `CanonicalKronosHours` | `SinkKronosHours` |
| site | `CanonicalKronosSite` | `SinkSite`, `SinkRegion`, `SinkSiteBusinessUnit` |

Submission: `data_platform/flink_job/start_flink_job.sh <name>` or `start_flink_job_all.py`

### Stage 3 — Kafka Connect JDBC Sink

One JDBC Sink connector per PDM table. The `ChangeCase` SMT converts Avro camelCase field names to MySQL snake_case. `register_connectors.py` builds connector configs programmatically and POSTs them to the Kafka Connect REST API.

MySQL ODS database: `retail_ops` · user: `connect_user` · DDL: `data_platform/ddl/`

### Stage 4 — Debezium CDC

A single Debezium MySQL source connector reads the MySQL ODS binlog and emits Debezium-envelope messages to CDC topics:

```
retail_ops.aurora.retail_ops.sales_orders
retail_ops.aurora.retail_ops.appointments
retail_ops.aurora.retail_ops.pos_invoices
retail_ops.aurora.retail_ops.work_orders
retail_ops.aurora.retail_ops.article_inventory
```

Envelope: `{ "before": {...}, "after": {...}, "op": "c|u|d|r", "ts_ms": 123 }`

### Stage 5 — Spark Streaming → MinIO Landing (Iceberg)

`cdc_to_landing.py` subscribes to all CDC topics and appends the full Debezium envelope as rows to Iceberg landing tables. Key properties:

- Materialization: **append-only** — full CDC history preserved
- Checkpoint: `s3a://checkpoints/cdc/<table>`
- Catalog: Iceberg REST at `http://iceberg-rest:8181`
- Partition: by `days(ingested_at)`

### Stage 6 — dbt Lakehouse Transformations

dbt Core (dbt-spark, Thrift Server :10000) runs 4 transformation layers:

| Layer | Materialization | CDC handling |
|-------|----------------|-------------|
| **staging** | view | Select from `source('landing', …)`, filter tombstones |
| **bronze** | incremental / append | Flatten `after_json`/`before_json`, tag `_cdc_op` |
| **silver** | incremental / merge | MERGE by PK; `delete_cdc_rows` post-hook for deletes |
| **gold** | table | Join all 5 silver entities into `gold_store_kpis` |
| **analytics** | table | Rolling windows, RFM, churn risk from gold |

Airflow `dbt_lakehouse_pipeline` DAG schedules bronze→silver→gold→analytics every 30 minutes.

### Stage 7 — Analytics / ML / LLM on Lakehouse

| Component | Description |
|-----------|-------------|
| **Feast Feature Store** | Offline store reads `iceberg.analytics.*`; materializes to Redis online store for low-latency ML feature serving |
| **Qdrant Vector Index** | `store_kpi_narratives` — per-store KPI text embeddings; `metric_definitions` — business metric descriptions for AI reasoning |
| **MetricFlow Semantic Layer** | 9 named metrics (`revenue_total`, `appointment_show_rate`, `refund_rate`, etc.) queryable by `store_id` + `kpi_date` |

## Data conventions

| Concept | Pattern |
|---------|---------|
| Canonical Kafka topic | `Canonical<Domain><Entity>` |
| PDM Sink Kafka topic | `Sink<Entity>` |
| CDC Kafka topic | `retail_ops.aurora.retail_ops.<table>` |
| Iceberg landing | `iceberg.landing.<table>` |
| Iceberg bronze | `iceberg.bronze.<table>` |
| Iceberg silver | `iceberg.silver.<table>` |
| Iceberg gold | `iceberg.gold.gold_store_kpis` |
| Iceberg analytics | `iceberg.analytics.feat_<name>` |
| Feast online key | `store_id` or `customer_id` (Redis DB 1) |
| Qdrant collections | `store_kpi_narratives`, `metric_definitions` |
