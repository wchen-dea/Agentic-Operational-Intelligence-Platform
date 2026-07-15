# AI Systems Architecture

The AI layer reads from two sources in parallel:
- **Real-time path** — MySQL ODS directly (Stage 4 of the data pipeline)
- **Lakehouse path** — Iceberg gold/analytics + Qdrant + Feast (Stages 7–8)

## Component overview

```mermaid
graph TB
    subgraph Sources["Data Sources"]
        MYSQL["MySQL ODS :3306\nreal-time KPI path"]
        GOLD["iceberg.gold.gold_store_kpis\nlakehouse path"]
        FEAST["Feast :6566\nML online features (Redis)"]
        QDRANT["Qdrant :6333\nvector embeddings"]
        SEMLAY["MetricFlow\nsemantic layer metrics"]
    end

    subgraph API["Services Layer :8000"]
        REST["FastAPI REST\n/ask /kpi /alerts /operations /skills"]
        MCP["MCP Server\n5 tools · 2 resources · 2 prompts"]
        SCHED["Scheduler\nPeriodic briefs"]
    end

    subgraph Guardrails["Guardrails"]
        INJ["Prompt Injection Detection\n7 regex patterns"]
        PII["PII Scrubbing\nSSN · credit card · email · phone"]
        OUT["Output Quality Validation\nblocked content · hallucination check"]
    end

    subgraph Orchestration["Agent Orchestration"]
        IR["Intent Router (Haiku)\nKPI · Anomaly · Promotion · Brief · QA"]
        DAG["DAG Builder\nMinimal subgraph extraction"]
        EXEC["DAG Executor\nTier-parallel · Retry · Fallback · Trace"]
    end

    subgraph Context["Hybrid Context Assembly"]
        SSS["StreamingStateStore\nRedis / in-process TTL cache"]
        HYB["LocalHybridSearch\nChromaDB + TF-IDF · RRF fusion"]
        MEM["PersistentSessionMemory\nSQLite / DynamoDB · TTL"]
    end

    subgraph Agents["Specialized Agents"]
        KPI["KPI Agent\nFetch + semantic enrich"]
        ANO["Anomaly Agent\nThreshold breach · trend detection"]
        PRO["Promotion Agent\nBranded mix · promo readiness"]
        REC["Recommendation Agent\nPersona-aware brief generation"]
    end

    subgraph Skills["Skill Registry"]
        SK1["fetch_kpis"]
        SK2["detect_anomalies"]
        SK3["semantic_search"]
        SK4["diagnose_signals"]
        SK5["generate_narrative"]
    end

    subgraph LLM["LLM Layer"]
        MR["ModelRouter\nHaiku → Sonnet → Opus"]
        CL["Anthropic Claude\nSync · Async · Stream · Vision · Tools"]
        CACHE["LRU Response Cache\n128 entries · SHA-256 keyed"]
        STRUCT["Structured Output\nPydantic KPIInsight · OperationalBriefResponse\nAnomalyDiagnosisResponse · PromotionRecommendation"]
        PR["Prompt Registry\nVersioned · Lifecycle · A/B Variants"]
    end

    MYSQL --> REST
    GOLD --> REST
    FEAST -->|"online features"| REST
    QDRANT -->|"semantic search"| SK3
    SEMLAY --> REST

    REST --> INJ --> PII --> IR
    IR --> DAG --> EXEC
    EXEC --> Context
    EXEC --> KPI & ANO & PRO & REC
    KPI & ANO & PRO & REC --> Skills
    Skills --> MR --> CL --> STRUCT
    CL --> CACHE
    CL --> PR
    EXEC --> OUT
```

## Agent DAG execution flow

```mermaid
sequenceDiagram
    actor User as Store Manager / Executive
    participant API as FastAPI REST
    participant GR as Guardrails
    participant IR as Intent Router (Haiku)
    participant DAG as DAG Builder
    participant CTX as Hybrid Context Assembler
    participant KPI as KPI Agent
    participant ANO as Anomaly Agent
    participant PRO as Promotion Agent
    participant REC as Recommendation Agent (Sonnet)
    participant OBS as Observability Tracker
    participant MEM as Session Memory

    User->>API: POST /ask {question, session_id, persona}
    API->>GR: injection check + PII scrub
    GR-->>API: sanitized query

    API->>IR: classify intent
    IR-->>API: intent=brief  agents=[kpi,anomaly,promotion,recommendation]

    API->>DAG: build subgraph for intent
    DAG-->>API: tier-ordered node list

    API->>CTX: assemble context window
    CTX->>CTX: fetch streaming KPIs (Redis / in-process)
    CTX->>CTX: vector + keyword search (ChromaDB + TF-IDF RRF)
    CTX->>MEM: load session history
    CTX-->>API: ContextWindow {kpis, docs, history}

    Note over API: Phase 0 complete — context ready

    API->>KPI: execute(context)
    KPI-->>OBS: emit latency + tokens
    KPI-->>API: KPIInsights

    API->>ANO: execute(kpi_insights)
    ANO-->>OBS: emit latency + tokens
    ANO-->>API: AnomalyReport

    API->>PRO: execute(kpi_insights, anomalies)
    PRO-->>OBS: emit latency + tokens
    PRO-->>API: PromotionAnalysis

    API->>REC: execute(all_results, persona)
    REC->>REC: compact prompt construction
    REC->>REC: generate_with_tools() — skill loop
    REC-->>OBS: emit latency + tokens + cost
    REC-->>API: OperationalBrief

    API->>MEM: persist turn (question + brief)
    API->>OBS: LLM quality evaluation (rule-based + LLM-as-judge)
    API-->>User: {brief, kpis, anomalies, promotions, execution_trace}
```

## Intent → agent subgraph mapping

| Intent | Triggered agents | API endpoints |
|--------|-----------------|--------------|
| `kpi_query` | kpi, rag_search | `/kpi`, `/kpi/enriched` |
| `anomaly_check` | kpi, anomaly, rag_search | `/alerts/{store_id}` |
| `promotion_analysis` | kpi, anomaly, promotion, rag_search | — |
| `operational_brief` | kpi, anomaly, promotion, recommendation, rag_search | `/operations/brief` |
| `general_qa` | all | `/ask`, `/ask/agentic` |

## Production AI stack

| Layer | Role | Implementation |
|-------|------|---------------|
| **LLM** | Natural-language generation, intent classification, diagnosis | Anthropic Claude (`claude-sonnet-4`) · `ModelRouter` (Haiku → Sonnet → Opus) · `ai_layer/llm.py` |
| **Vector Database** | Semantic search over operational knowledge corpus | ChromaDB (persistent) + TF-IDF (sparse) with reciprocal rank fusion · `ai_layer/rag/` |
| **Long-term AI search** | KPI narrative search, metric definition lookup | Qdrant `store_kpi_narratives` + `metric_definitions` · `data_platform/vector_index/` |
| **Feature serving** | Low-latency ML feature retrieval for inference | Feast online store (Redis) · `data_platform/feature_store/` |
| **Semantic metrics** | Dimension-aware business metric queries | dbt MetricFlow 9 named metrics · `data_platform/dbt/models/semantic/` |
| **Orchestration** | DAG-based agent execution with intent routing | `ai_layer/orchestration/` — dag, router, executor |
| **Skills** | Composable LLM tool-calling capabilities | `ai_layer/skills/` — SkillRegistry + 5 built-in skills |
| **Guardrails** | Input validation, output quality enforcement | `ai_layer/guardrails.py` |
| **Memory** | Multi-turn session coherence | `ai_layer/memory/persistent_memory.py` (SQLite) |
| **Prompts** | Versioned, A/B-tested prompt templates | `ai_layer/prompts.py` — PromptRegistry + ExperimentManager |
| **Structured output** | Typed, validated LLM responses | `ai_layer/structured_output.py` — Pydantic models |

## Design principle

Swapping the underlying LLM requires only one config change (`config/settings.py`). Every other layer — retrieval, orchestration, evaluation, memory, guardrails — stays unchanged.

```mermaid
graph LR
    subgraph "Data Quality"
        CDC["CDC + Flink\nClean canonical events"]
        MED["Iceberg Lakehouse\nVersioned KPI rollups"]
    end
    subgraph "Retrieval Quality"
        VDB["ChromaDB + Qdrant\nHybrid RRF search"]
        MEM2["Persistent Memory\nSession coherence"]
    end
    subgraph "Orchestration Quality"
        DAGQ["DAG Executor\nIntent routing · Circuit breaker"]
        SKLQ["Skill Registry\nComposable · Observable"]
    end
    subgraph "Output Quality"
        GRDQ["Guardrails\nInjection · PII · Quality"]
        EVLQ["Evaluator\nGroundedness · Relevance · Persona"]
    end
    subgraph "Model Layer"
        LLMQ["Claude Haiku / Sonnet / Opus\n(swappable one-line config)"]
    end

    CDC --> MED --> VDB
    VDB --> DAGQ
    MEM2 --> DAGQ
    DAGQ --> SKLQ --> LLMQ
    LLMQ --> GRDQ --> EVLQ
```

## API endpoints

| Endpoint | Method | Description | Auth role |
|----------|--------|-------------|-----------|
| `/ask` | POST | Agentic Q&A — guardrails → intent routing → DAG execution | operator |
| `/ask/stream` | POST | SSE streaming Q&A | operator |
| `/ask/async` | POST | Non-blocking async generation | operator |
| `/ask/agentic` | POST | Tool-calling queries with skill invocation | operator |
| `/kpi` | POST | Fetch KPIs for a store or region | viewer |
| `/kpi/enriched` | POST | KPIs with semantic metadata and anomaly flags | viewer |
| `/kpi/catalog` | GET | Machine-readable KPI catalog (16 definitions) | viewer |
| `/alerts/{store_id}` | GET | Active alerts for a store | viewer |
| `/operations/brief` | POST | Persona-aware operational brief | operator |
| `/skills` | GET | List all agent skills with tool schemas | operator |
| `/skills/{name}/invoke` | POST | Invoke a skill by name | operator |
| `/usage` | GET | LLM token usage and session cost | admin |
| `/metrics` | GET | Prometheus exposition format | admin |
| `/health` | GET | Health check | public |

## Architecture decision records

| ADR | Decision | Status |
|-----|----------|--------|
| [ADR-011](adr/011-anthropic-claude-as-llm.md) | Anthropic Claude as LLM — Haiku/Sonnet/Opus routing with fallback | Accepted |
| [ADR-013](adr/013-persona-aware-orchestration.md) | Persona-aware orchestration (`store_manager` / `executive`) | Accepted |
| [ADR-015](adr/015-agent-skill-framework.md) | Skill ABC + SkillRegistry with auto-instrumented invocation | Accepted |
| [ADR-014](adr/014-dag-orchestration-intent-routing.md) | DAG-based execution with intent routing and tier-parallel agents | Accepted |
| [ADR-016](adr/016-hybrid-context-assembly.md) | Hybrid context: streaming state + vector retrieval + session memory | Accepted |
| [ADR-017](adr/017-llmops-prompt-versioning.md) | Versioned PromptRegistry + A/B ExperimentManager | Accepted |
| [ADR-018](adr/018-token-cost-efficiency.md) | LRU response cache, per-call UsageTracking, compact prompts | Accepted |
