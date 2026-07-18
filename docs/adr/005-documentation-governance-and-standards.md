# ADR-005: Documentation Governance and Standards

## Status

Accepted

## Context

Project documentation grew across architecture guides, runbooks, ADRs, and operational references. Prior updates introduced drift in naming conventions, inconsistent section structures, and terminology mismatches across files. This creates onboarding friction and increases the risk of operational errors when procedures are copied from outdated docs.

The project needs a durable documentation governance decision that standardizes:

- Canonical terminology.
- Markdown file naming and link conventions.
- Shared section structure for architecture docs and ADRs.
- Change discipline for large documentation refactors.

## Decision

Adopt a documentation governance baseline with two canonical standards documents:

- `docs/terminology-glossary.md` as the source of truth for platform terms.
- `docs/markdown-structure-standard.md` as the source of truth for formatting and section order.

Governance rules:

- Architecture, runbook, and ADR documents must include references to the glossary and structure standard.
- Documentation filenames use kebab-case and internal links must match canonical targets.
- Structural refactors should update index documents (`README.md`, `docs/adr/README.md`) in the same change.
- Editorial normalization passes are allowed when they do not modify technical meaning.

## Alternatives considered

| Option                     | Reason not chosen                                                                      |
| -------------------------- | -------------------------------------------------------------------------------------- |
| No formal documentation ADR | Drift recurs and standards become implicit knowledge                                  |
| Per-team style guides       | Inconsistent standards across subsystems and unclear ownership for cross-cutting docs |
| Tool-only lint enforcement  | Useful for syntax, but insufficient for terminology and architecture narrative quality |

## Consequences

### Positive

- Readers get consistent terminology and predictable structure across major project docs.
- Refactors become safer because index/link consistency is treated as part of definition-of-done.
- ADR quality improves by keeping rationale format and consequence framing uniform over time.

### Negative / trade-offs

- Contributors must spend additional time validating links and structure in documentation-heavy changes.
- Governance introduces editorial overhead for fast prototyping branches before merge.

### Neutral / constraints

- Standards define minimum consistency requirements but do not prevent domain-specific detail where needed.
- Existing documents can be normalized incrementally; full rewrite is not required for every change.

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](../terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](../markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
