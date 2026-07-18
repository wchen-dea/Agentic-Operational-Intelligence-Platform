# Markdown Structure Standard

This standard defines structural formatting expectations for AOIP Markdown documents.

## Required Structure

- Exactly one H1 title at the top of the document.
- Use H2 sections for major topics.
- Use H3 sections only when needed for sub-procedures.
- Prefer ordered lists for procedures and unordered lists for references.
- Keep section titles in Title Case.

## Formatting Rules

- Use fenced code blocks with language labels when possible (for example `bash`, `json`, `yaml`).
- Keep table headers concise and semantic.
- Keep line wrapping and list formatting consistent through Prettier.
- Use relative links for project documents.
- Keep terminology aligned with the shared glossary.

## Canonical References

- Terminology definitions: [Terminology Glossary](terminology-glossary.md)
- Operational procedures: [Runbook](runbook.md)
- System-level architecture map: [System Overview](system-overview.md)

## Section Order Templates

Apply these section sequences by document type.

### README

1. H1 Title
2. Platform Summary
3. Pipeline Architecture
4. Documentation Index
5. Quick Start
6. Environment or Provider Profiles
7. Repository Layout
8. Operational Commands
9. Terminology Glossary
10. Structural Formatting Standard

### Architecture Documents

1. H1 Title
2. Scope and Purpose
3. Architecture Overview
4. Components and Responsibilities
5. Data or Control Flow
6. Operational Considerations
7. Cross References
8. Terminology Glossary
9. Structural Formatting Standard

### ADR Documents

1. H1 Title
2. Status
3. Context
4. Decision
5. Alternatives Considered
6. Consequences
7. Terminology Glossary
8. Structural Formatting Standard

### Runbook

1. H1 Title
2. Operating Principles
3. Prerequisites
4. Procedures
5. Incident Playbooks
6. Rollback and Recovery
7. Reference Endpoints
8. Terminology Glossary
9. Structural Formatting Standard

### Metrics and Reference Catalogs

1. H1 Title
2. Metric or Reference Definitions
3. Thresholds and Interpretation
4. Usage Notes
5. Terminology Glossary
6. Structural Formatting Standard

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document defines the shared markdown structure standard for AOIP documentation.
