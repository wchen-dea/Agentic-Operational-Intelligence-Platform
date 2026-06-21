# ADR-009: Hybrid Context Assembly (Streaming + Vector + Memory)

## Status

Accepted

## Context

Agents consumed context from a single source (RAG retrieval). Real-time streaming signals, session history for multi-turn coherence, and vector search results were not unified, leading to incomplete context and inability to reference previous turns.

## Decision

Introduce `HybridContextAssembler` (`ai_layer/context.py`) that merges three context sources into a unified `ContextWindow`:

- **`StreamingStateStore`** — TTL-based in-process cache for real-time KPI snapshots and alert state. In production, fronts Redis or a Kafka consumer.
- **`SessionMemory`** — sliding-window conversational memory per session for multi-turn coherence. Configurable max turns with automatic eviction.
- **Vector/keyword retrieval** — existing `LocalHybridSearch` via the RAG corpus.

## Consequences

- Agents receive a single `ContextWindow` combining real-time state, retrieved documents, and conversation history.
- Session memory enables follow-up questions without re-stating context.
- Streaming state provides sub-second freshness for KPI snapshots.
- Production deployments should replace `StreamingStateStore` with Redis and `SessionMemory` with a persistent store.
