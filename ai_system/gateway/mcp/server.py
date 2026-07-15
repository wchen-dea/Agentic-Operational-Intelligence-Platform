"""Model Context Protocol (MCP) server - exposes platform tools and resources.

Any MCP-compatible client (Claude Desktop, VS Code Copilot, etc.) can connect
to this server and invoke the platform's skills, query KPIs, and search the
knowledge base.

Run standalone::

    uv run python -m mcp_server
"""

import json
import logging

from mcp.server.fastmcp import FastMCP

from ai_system.tools.fetch_kpi_tool import fetch_store_kpis
from ai_system.tools.alert_tool import detect_kpi_alerts_for_store
from ai_system.retrieval.hybrid_search import LocalHybridSearch
from ai_system.config.settings import settings
from data_platform.semantic_layer import enrich_kpis, _load_kpi_catalog

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Agentic Operational Intelligence Platform",
    description="Retail operational intelligence - KPIs, alerts, knowledge base, and diagnostics.",
)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def get_store_kpis(store_id: str) -> str:
    """Retrieve current KPI metrics for a specific store.

    Returns key performance indicators including revenue, conversion rates,
    appointment show rates, inventory health, and work order metrics.
    """
    kpis = fetch_store_kpis(store_id=store_id)
    if not kpis:
        return json.dumps({"error": f"No data found for store {store_id}"})
    return json.dumps(kpis, indent=2)


@mcp.tool()
def get_region_kpis(region: str) -> str:
    """Retrieve aggregated KPI metrics for all stores in a region.

    Returns region-level averages and totals across all stores.
    """
    kpis = fetch_store_kpis(region=region)
    if not kpis:
        return json.dumps({"error": f"No data found for region {region}"})
    return json.dumps(kpis, indent=2)


@mcp.tool()
def get_enriched_kpis(store_id: str) -> str:
    """Retrieve KPIs with semantic metadata (unit, direction, thresholds, anomaly flags).

    Each KPI includes whether it's anomalous and a human-readable description.
    """
    raw = fetch_store_kpis(store_id=store_id)
    if not raw:
        return json.dumps({"error": f"No data found for store {store_id}"})
    snapshot = enrich_kpis(raw)
    return json.dumps(
        {
            "store_id": snapshot.store_id,
            "records": [r.to_dict() for r in snapshot.records],
            "anomalies": [r.name for r in snapshot.anomalous_records],
        },
        indent=2,
    )


@mcp.tool()
def detect_alerts(store_id: str) -> str:
    """Detect threshold breaches and anomalies for a specific store.

    Evaluates current KPIs against configured rules and returns active alerts
    with severity, description, and remediation guidance.
    """
    kpis = fetch_store_kpis(store_id=store_id)
    if not kpis or "store_id" not in kpis:
        return json.dumps({"error": f"No KPI data for store {store_id}"})
    alerts = detect_kpi_alerts_for_store(kpis, settings.alert_rules_path)
    return json.dumps({"store_id": store_id, "alert_count": len(alerts), "alerts": alerts}, indent=2)


@mcp.tool()
def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """Search the operational knowledge base for relevant playbooks and guidance.

    Uses hybrid TF-IDF + vector search to find the most relevant documents.

    Args:
        query: The search query text.
        top_k: Number of results to return (default 3).
    """
    searcher = LocalHybridSearch(settings.rag_corpus_path)
    results = searcher.search(query, top_k=top_k)
    return json.dumps(results, indent=2)


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("kpi://catalog")
def kpi_catalog_resource() -> str:
    """The complete KPI catalog with definitions, formulas, and thresholds."""
    catalog = _load_kpi_catalog()
    return json.dumps(list(catalog.values()), indent=2)


@mcp.resource("config://thresholds")
def threshold_rules_resource() -> str:
    """Current alert threshold rules with severity and remediation guidance."""
    from ai_system.tools.alert_tool import load_rules

    rules = load_rules(settings.alert_rules_path)
    return json.dumps(rules, indent=2)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


@mcp.prompt()
def operational_brief(store_id: str, persona: str = "store_manager") -> str:
    """Generate an operational brief prompt for a store."""
    return (
        f"You are an operational intelligence assistant for a retail chain.\n"
        f"Analyze the KPIs for store {store_id} and provide an actionable brief "
        f"tailored for a {persona}.\n\n"
        f"Include: key findings, anomalies, root causes, and priority actions "
        f"with expected impact and time horizon."
    )


@mcp.prompt()
def anomaly_investigation(store_id: str, metric: str) -> str:
    """Generate an anomaly investigation prompt for a specific metric."""
    return (
        f"Investigate why {metric} is anomalous for store {store_id}.\n\n"
        f"1. Fetch the current KPIs for the store\n"
        f"2. Check for active alerts\n"
        f"3. Search the knowledge base for relevant guidance\n"
        f"4. Provide root cause analysis and recommended actions"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
