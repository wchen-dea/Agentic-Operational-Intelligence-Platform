# ADR-009: Hybrid Context Assembly (Streaming + Vector + Memory)

## Status

Accepted

## Context

Agents consumed context from a single source (RAG retrieval). Real-time streaming signals, session history for multi-turn coherence, and vector search results were not unified, leading to incomplete context and inability to reference previous turns.

## Decision

Introduce `HybridContextAssembler` (`ai_layer/context.py`) that merges three context sources into a unified `ContextWindow`:

- **`StreamingStateStore`** — TTL-based in-process cache for real-time KPI snapshots and alert state. In production, fronts Redis or a Kafka consumer.
- **`SessionMemory`** — sliding-window conversational memory per session for multi-turn coherence. Configurable max turns with automatic eviction.
- **`PersistentSessionMemory`** (`ai_layer/memory/persistent_memory.py`) — SQLite-backed session memory that survives process restarts with TTL-based expiration and cross-session knowledge accumulation. Drop-in replacement for `SessionMemory`.
- **Vector/keyword retrieval** — `LocalHybridSearch` combining ChromaDB vector embeddings with TF-IDF keyword search and reciprocal rank fusion. Supports domain and persona metadata filtering.

## Consequences

- Agents receive a single `ContextWindow` combining real-time state, retrieved documents, and conversation history.
- Session memory enables follow-up questions without re-stating context.
- Persistent memory survives restarts and enables cross-session knowledge accumulation.
- Streaming state provides sub-second freshness for KPI snapshots.
- ChromaDB vector search improves semantic retrieval quality over TF-IDF alone.
- Production deployments should replace `StreamingStateStore` with Redis and `PersistentSessionMemory` backend with DynamoDB for horizontal scaling.
