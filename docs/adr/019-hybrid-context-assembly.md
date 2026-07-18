# ADR-019: Hybrid Context Assembly (Streaming + Vector + Memory)

## Status

Accepted

## Context

LLM quality degrades when the model lacks relevant context. The platform has three distinct context sources: (1) real-time KPI snapshots from the streaming state store, (2) relevant knowledge documents from the RAG corpus, and (3) conversational history from session memory. Separately queried, these sources produce redundant API calls and inconsistent context windows. A unified assembly layer ensures every agent receives the same context window.

## Decision

Implement a **`HybridContextAssembler`** (`ai_systems/retrieval/context.py`) that merges three sources into a single `ContextWindow` object consumed by all agents:

1. **`StreamingStateStore`** (in-process TTL cache, or `RedisStreamingStateStore` for production) — holds real-time KPI snapshots and CDC event summaries. TTL: 300 s default.

2. **`LocalHybridSearch`** (`ai_systems/retrieval/hybrid_search.py`) — combines:
   - ChromaDB vector search (semantic similarity, 384-dim embeddings).
   - TF-IDF keyword search (exact term recall).
   - **Reciprocal Rank Fusion (RRF)** to merge results without tuning score thresholds.

3. **`PersistentSessionMemory`** (SQLite-backed, TTL-aware) — maintains recent conversation turns per session. Sliding window (last 20 turns). Production: swap backend for DynamoDB or Redis.

The assembled `ContextWindow(streaming, retrieval, memory)` is passed to every agent node in Phase 0 of the DAG execution, before any LLM calls.

## Alternatives considered

| Option                          | Reason not chosen                                                             |
| ------------------------------- | ----------------------------------------------------------------------------- |
| Pure vector search (no keyword) | Misses exact-match queries (store IDs, SKU codes, metric names)               |
| Pure keyword search (no vector) | Misses semantic queries ("stores with poor inventory health")                 |
| LangChain RetrievalQA           | Black-box; no control over fusion strategy; couples context to LangChain      |
| Pinecone / Weaviate             | Adds external dependency; ChromaDB + TF-IDF is sufficient for the corpus size |

## Consequences

### Positive

- RRF fusion eliminates the need to tune score thresholds for combining vector and keyword results.
- `StreamingStateStore` TTL expiry prevents stale KPI data from reaching agents.
- `PersistentSessionMemory` survives process restarts — multi-turn sessions are coherent across API server restarts.
- The `ContextWindow.is_empty` property allows agents to skip context injection for fresh sessions.

### Negative / trade-offs

- ChromaDB in-process mode is not horizontally scalable — in multi-replica deployments, the corpus must be pre-loaded on each replica or moved to a shared store.
- TF-IDF vectorizer is rebuilt in memory on startup — large corpora add startup latency.
- `PersistentSessionMemory` SQLite writes are synchronous — high concurrency may cause lock contention.

### Neutral / constraints

- `AOIP_CHROMA_PERSIST_PATH` controls ChromaDB persistence; unset = ephemeral in-process store (dev/test).
- The session TTL (`AOIP_REDIS__SESSION_TTL_SECONDS`, default 86400 s) controls how long session turns are retained.

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](../terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](../markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
