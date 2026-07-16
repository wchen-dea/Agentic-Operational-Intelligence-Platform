# ADR-021: Model Context Protocol (MCP) Server for External Tool Integration

## Status

Accepted

## Context

Beyond the REST API, the platform should be usable by external AI systems and development tools (Claude Desktop, VS Code Copilot, Cursor, etc.) that support the Model Context Protocol. MCP enables external agents to discover and invoke platform capabilities as structured tools, access live resources (KPI catalog, threshold config), and use managed prompts — without knowing the platform's REST API surface.

## Decision

Implement an **MCP server** (`ai_systems/gateway/mcp/server.py`) using the `mcp` Python SDK (version 1.10+). The server exposes:

**5 tools:**
| Tool | Description |
|------|-------------|
| `get_store_kpis` | Fetch KPI metrics for a specific store |
| `get_region_kpis` | Fetch aggregated KPIs for a region |
| `get_enriched_kpis` | KPIs with anomaly flags and semantic metadata |
| `detect_alerts` | Retrieve active threshold breaches for a store |
| `search_knowledge_base` | Semantic + keyword search over the knowledge corpus |

**2 resources:**
| Resource | URI | Content |
|----------|-----|---------|
| KPI catalog | `kpi://catalog` | Machine-readable KPI definitions (YAML) |
| Alert thresholds | `config://thresholds` | Threshold rules with severity and remediation |

**2 prompts:**
| Prompt | Description |
|--------|-------------|
| `operational_brief` | Persona-aware operational brief generation prompt |
| `anomaly_investigation` | Structured anomaly root-cause investigation prompt |

The MCP server runs as a separate Python process alongside the FastAPI app.

## Alternatives considered

| Option | Reason not chosen |
|--------|------------------|
| REST API only (no MCP) | External AI agents cannot auto-discover capabilities; requires custom integration per tool |
| GraphQL API | Not supported by MCP clients; adds schema maintenance overhead |
| OpenAI function definitions | Anthropic/Claude-native format; MCP is provider-agnostic |

## Consequences

### Positive
- Any MCP-compatible client (Claude Desktop, VS Code Copilot, Cursor) can use platform tools without custom REST integration.
- Tool schemas are auto-generated from Python type hints — no manual JSON schema maintenance.
- Resources expose live data (YAML at runtime) — KPI catalog and threshold changes are reflected immediately without client restart.

### Negative / trade-offs
- MCP is a relatively new protocol — client compatibility varies; fallback to REST API is required for non-MCP consumers.
- The MCP server runs as a separate process — requires coordinating startup with the FastAPI API server.

### Neutral / constraints
- MCP transport: stdio (default) or HTTP SSE — configured at server startup.
- Tool implementations delegate to the same skill registry as the FastAPI API, ensuring consistent behaviour across both surfaces.
