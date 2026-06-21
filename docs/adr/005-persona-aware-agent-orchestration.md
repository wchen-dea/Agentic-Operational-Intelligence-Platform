# ADR-005: Persona-Aware Agent Orchestration

## Status

Accepted

## Context

Store managers and executives have different decision horizons, action authority, and information needs. A single undifferentiated response reduces relevance for both audiences.

## Decision

The orchestrator accepts a `persona` parameter (`store_manager` or `executive`) that shapes:

- The recommendation agent's strategic playbook framing
- The operational brief's priority actions and owners
- The LLM system prompt tone and focus

## Consequences

- API consumers must specify persona; defaults to `store_manager`.
- Adding new personas (e.g., `regional_manager`) requires updating the recommendation agent's conditional logic.
- Persona-specific output is testable: the test suite asserts that executive responses contain strategic language.
- UX layers can auto-select persona based on user role without backend changes.
