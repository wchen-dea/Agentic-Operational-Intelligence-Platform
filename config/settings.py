from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AuroraMySQLSettings(BaseModel):
    host: str = "aurora-cluster.cluster-xxxxxxxxxxxx.us-east-1.rds.amazonaws.com"
    port: int = 3306
    database: str = "retail_ops"
    username: str = "aurora_app_user"
    password_secret_name: str = "aurora/mysql/app-user"
    sales_order_table: str = "sales_orders"
    appointment_table: str = "appointments"
    pos_invoice_table: str = "pos_invoices"
    work_order_table: str = "work_orders"
    inventory_table: str = "inventory_snapshots"


class CDCSettings(BaseModel):
    mode: str = "aurora_mysql_cdc"
    transport: str = "kafka_msk"
    connector: str = "aws_dms"
    topic_prefix: str = "retail_ops.aurora"
    checkpoint_location: str = "dbfs:/checkpoints/aurora_mysql_cdc"
    watermark_delay_seconds: int = 60


class LakehouseSettings(BaseModel):
    bronze_schema: str = "bronze"
    silver_schema: str = "silver"
    gold_schema: str = "gold"


class LLMSettings(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1024
    temperature: float = 0.3
    api_key_env_var: str = "ANTHROPIC_API_KEY"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AOIP_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "Agentic Operational Intelligence Platform"
    rag_corpus_path: str = str(_PROJECT_ROOT / "ai_layer/rag/data/sample_corpus.jsonl")
    alert_rules_path: str = str(_PROJECT_ROOT / "alerts/rules/kpi_thresholds.yaml")
    default_region: str = "Phoenix"
    aurora_mysql: AuroraMySQLSettings = AuroraMySQLSettings()
    cdc: CDCSettings = CDCSettings()
    lakehouse: LakehouseSettings = LakehouseSettings()
    llm: LLMSettings = LLMSettings()


settings = Settings()
