# ADR-004: Medallion Lakehouse Architecture

## Status

Accepted

## Context

Raw CDC events need progressive refinement before they're useful for KPI aggregation, alerting, and AI agent consumption. A clear layering strategy prevents coupling between ingestion concerns and business logic.

## Decision

Adopt the medallion (bronze → silver → gold) pattern on Delta Lake:

| Layer | Schema | Content |
|-------|--------|---------|
| Bronze | `bronze` | Raw CDC events with full payload (`<table>_cdc`) |
| Silver | `silver` | Normalized domain tables (`<table>`) |
| Gold | `gold` | Aggregated KPI rollups (`<business_subject>`) |

## Consequences

- Clear separation of concerns: ingestion, normalization, and business aggregation are independently testable.
- Bronze tables are append-only and replayable.
- Silver tables support MERGE/upsert for late-arriving events.
- Gold tables are the sole input for the AI orchestrator and alert engine.
- Storage costs increase with redundancy; lifecycle policies should expire old bronze data.
