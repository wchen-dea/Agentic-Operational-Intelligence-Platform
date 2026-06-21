from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "Agentic Operational Intelligence Platform"
    rag_corpus_path: str = "ai_layer/rag/data/sample_corpus.jsonl"
    alert_rules_path: str = "alerts/rules/kpi_thresholds.yaml"
    default_region: str = "Phoenix"

settings = Settings()
