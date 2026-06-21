# Copilot UI Module

## Target Status Alignment

This module should implement the user-facing experience for `agentic-operational-intelligence-platform`.

## Recommended Implementation

- React or Next.js chat interface
- Store Manager dashboard widgets
- Executive rollup cards
- Alert timeline
- Promotion recommendation panel

## API Integration Priority

Implement these API flows in order:

1. `POST /operations/brief` for persona-specific operational readouts.
2. `POST /ask` for agentic Q&A and strategy refinement.
3. `POST /kpi` and `GET /alerts/{store_id}` for drill-down support widgets.
