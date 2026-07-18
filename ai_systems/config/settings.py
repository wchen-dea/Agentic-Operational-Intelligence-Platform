"""Module for settings."""

from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class AuroraMySQLSettings(BaseModel):
    """MySQL connection settings.

    For local docker-compose development set via environment variables::

        AOIP_AURORA_MYSQL__HOST=mysql
        AOIP_AURORA_MYSQL__USERNAME=connect_user
        AOIP_AURORA_MYSQL__DATABASE=retail_ops

    The password is resolved from ``AURORA_PASSWORD`` env var first, then
    from AWS Secrets Manager using ``password_secret_name``.
    """

    host: str = "aurora-cluster.cluster-xxxxxxxxxxxx.us-east-1.rds.amazonaws.com"
    port: int = 3306
    database: str = "retail_ops"
    username: str = "aurora_app_user"
    password_secret_name: str = "aurora/mysql/app-user"


class CDCSettings(BaseModel):
    mode: str = "aurora_mysql_cdc"
    transport: str = "kafka_msk"
    connector: str = "aws_dms"
    topic_prefix: str = "cdc"
    checkpoint_location: str = "dbfs:/checkpoints/aurora_mysql_cdc"
    watermark_delay_seconds: int = 60


class LakehouseSettings(BaseModel):
    bronze_schema: str = "bronze"
    silver_schema: str = "silver"
    gold_schema: str = "gold"


class LLMSettings(BaseModel):
    # Supported providers: "anthropic" (default), "ollama" (local dev)
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1024
    temperature: float = 0.3
    # Used when provider == "anthropic"
    api_key_env_var: str = "ANTHROPIC_API_KEY"
    # Used when provider == "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout_seconds: float = 120.0


class RedisSettings(BaseModel):
    """Redis connection config for session memory and streaming state cache.

    Set ``url`` to a Redis connection string (e.g. ``redis://localhost:6379/0``
    or ``rediss://user:password@host:6380/0`` for TLS).
    Leave as ``None`` to fall back to the in-process store (development only).
    """

    url: str | None = None
    ttl_seconds: int = 300
    session_ttl_seconds: int = 86400  # 24 hours for session memory
    max_connections: int = 10


class TeamsSettings(BaseModel):
    """Microsoft Teams alert dispatch configuration.

    Set ``webhook_url`` to the Incoming Webhook URL created in the Teams
    channel where alerts should be posted.  Leave as ``None`` to disable
    Teams dispatch (alerts will only be logged).
    """

    webhook_url: str | None = None
    timeout_seconds: float = 10.0
    # Optional card theme colour (hex, no leading #)
    accent_color: str = "FF0000"


class OTelSettings(BaseModel):
    """OpenTelemetry distributed tracing configuration.

    Set ``enabled=true`` and provide an ``endpoint`` to activate tracing.
    When ``endpoint`` is None traces are collected but not exported (useful
    for local debugging with Jaeger UI).
    """

    enabled: bool = False
    endpoint: str | None = None  # OTLP gRPC, e.g. http://otel-collector:4317
    service_name: str = "aoip"
    traces_sample_rate: float = 1.0


class LoggingSettings(BaseModel):
    level: str = "INFO"
    json_format: bool = True  # Set false for human-readable local dev output


class Neo4jSettings(BaseModel):
    """Neo4j graph database connection settings."""

    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password_env_var: str = "NEO4J_PASSWORD"
    database: str = "neo4j"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AOIP_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # tolerate non-AOIP_ vars in .env (e.g. KAFKA_BROKERS, AURORA_PASSWORD)
    )

    app_name: str = "Agentic Operational Intelligence Platform"
    rag_corpus_path: str = str(_PROJECT_ROOT / "ai_systems/retrieval/corpus/sample_corpus.jsonl")
    alert_rules_path: str = str(_PROJECT_ROOT / "ai_systems/alerting/rules/kpi_thresholds.yaml")
    default_region: str = "Phoenix"
    # Set AOIP_CHROMA_PERSIST_PATH to persist the ChromaDB vector index to disk.
    # Leave as None to use an ephemeral in-process store (dev/test only).
    chroma_persist_path: str | None = None
    # KPI data source: "sqlite" (dev) | "aurora_mysql" | "delta_lake"
    kpi_source: str = "sqlite"
    # Required when kpi_source="delta_lake" - path/URI to the gold-layer Parquet root
    delta_lake_gold_path: str | None = None
    aurora_mysql: AuroraMySQLSettings = AuroraMySQLSettings()
    cdc: CDCSettings = CDCSettings()
    lakehouse: LakehouseSettings = LakehouseSettings()
    llm: LLMSettings = LLMSettings()
    redis: RedisSettings = RedisSettings()
    teams: TeamsSettings = TeamsSettings()
    otel: OTelSettings = OTelSettings()
    logging: LoggingSettings = LoggingSettings()
    neo4j: Neo4jSettings = Neo4jSettings()


settings = Settings()
