import logging
import os
from typing import Any

from ai_layer.llm import generate as llm_generate
from alerts.threshold_config import threshold_min, threshold_max

logger = logging.getLogger(__name__)


class RecommendationAgent:
    def _diagnose_signals(self, kpis: dict[str, Any], promo: dict[str, Any]) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []

        if kpis.get("revenue_total", float("inf")) < threshold_min("revenue_total", 1000):
            issues.append({
                "domain": "sales_order",
                "signal": "Low realized sales volume",
                "impact": "Under-performing store risk and lower daily contribution.",
            })
        if kpis.get("appointment_to_order_conversion_rate", 1.0) < threshold_min("appointment_to_order_conversion_rate", 0.25):
            issues.append({
                "domain": "appointment",
                "signal": "Low appointment-to-order conversion",
                "impact": "Weak conversion funnel and reduced promotion ROI.",
            })
        if kpis.get("pos_invoice_capture_rate", 1.0) < threshold_min("pos_invoice_capture_rate", 0.85):
            issues.append({
                "domain": "pos_invoice",
                "signal": "Low POS invoice capture",
                "impact": "Revenue realization leakage and unreliable downstream KPI analytics.",
            })
        if kpis.get("inventory_in_stock_rate", 1.0) < threshold_min("inventory_in_stock_rate", 0.90) or kpis.get("stockout_sku_count", 0) > threshold_max("stockout_sku_count", 3):
            issues.append({
                "domain": "inventory",
                "signal": "Inventory availability pressure",
                "impact": "Lost upsell opportunities and customer dissatisfaction due to stockouts.",
            })
        if kpis.get("average_work_order_cycle_time_minutes", 0.0) > threshold_max("average_work_order_cycle_time_minutes", 120):
            issues.append({
                "domain": "work_order",
                "signal": "Long work-order cycle time",
                "impact": "Lower same-day fulfillment capacity and weakened conversion confidence.",
            })
        if promo.get("promotion_signal", {}).get("low_branded_mix"):
            issues.append({
                "domain": "promotion",
                "signal": "Low branded revenue mix",
                "impact": "Margin expansion goals are at risk without targeted upsell tactics.",
            })
        return issues

    def build_operational_brief(
        self,
        kpis: dict[str, Any],
        alerts: list[dict[str, Any]],
        promo: dict[str, Any],
        context_docs: list[dict[str, Any]],
        persona: str = "store_manager",
    ) -> dict[str, Any]:
        issues = self._diagnose_signals(kpis, promo)

        priority_actions: list[dict[str, str]] = []
        if persona == "executive":
            priority_actions.append({
                "action": "Rank under-performing stores by revenue, conversion, and stockout pressure for intervention within 24 hours.",
                "owner": "Regional operations leader",
                "expected_impact": "Faster diagnosis and tighter cross-store execution.",
                "time_horizon": "24h",
            })
            priority_actions.append({
                "action": "Shift campaign budget to stores with healthy in-stock rates and strong appointment show rates.",
                "owner": "Commercial strategy",
                "expected_impact": "Higher promotion efficiency and lower wasted spend.",
                "time_horizon": "This week",
            })
        else:
            priority_actions.append({
                "action": "Run daily huddles on no-show appointments, overdue work orders, and stockout SKUs.",
                "owner": "Store manager",
                "expected_impact": "Improved operational stability and local conversion.",
                "time_horizon": "Daily",
            })
            priority_actions.append({
                "action": "Deploy branded upsell scripts for advisors on high-intent appointments and POS checkouts.",
                "owner": "Store team lead",
                "expected_impact": "Higher branded mix and improved margin quality.",
                "time_horizon": "This week",
            })

        for recommendation in promo.get("recommendations", [])[:3]:
            priority_actions.append({
                "action": recommendation,
                "owner": "Operations and promotion team",
                "expected_impact": "Reduced KPI variance and stronger conversion outcomes.",
                "time_horizon": "1-2 weeks",
            })

        severity_summary = {"high": 0, "medium": 0, "low": 0}
        for alert in alerts:
            severity = str(alert.get("severity", "medium"))
            if severity not in severity_summary:
                severity_summary[severity] = 0
            severity_summary[severity] += 1

        return {
            "persona": persona,
            "scope": {
                "store_id": kpis.get("store_id"),
                "region": kpis.get("region"),
            },
            "diagnosis": issues,
            "priority_actions": priority_actions,
            "alert_summary": {
                "total": len(alerts),
                "by_severity": severity_summary,
            },
            "kpi_watchlist": [
                "revenue_total",
                "appointment_to_order_conversion_rate",
                "pos_invoice_capture_rate",
                "inventory_in_stock_rate",
                "stockout_sku_count",
                "average_work_order_cycle_time_minutes",
                "branded_revenue_mix_rate",
            ],
            "retrieved_context_titles": [doc.get("title") for doc in context_docs],
        }

    def run(
        self,
        kpis: dict[str, Any],
        alerts: list[dict[str, Any]],
        promo: dict[str, Any],
        context_docs: list[dict[str, Any]],
        persona: str = "store_manager",
    ) -> str:
        store_or_region = kpis.get("store_id") or kpis.get("region") or "selected scope"
        issues = self._diagnose_signals(kpis, promo)
        lines = [
            f"Operational readout for {store_or_region}:",
            "",
            "Key KPI signals:",
        ]
        for metric in [
            "revenue_total", "order_count", "appointment_show_rate",
            "appointment_to_order_conversion_rate", "pos_invoice_capture_rate",
            "inventory_in_stock_rate", "stockout_sku_count", "branded_revenue_mix_rate",
            "average_work_order_cycle_time_minutes", "overdue_work_order_count"
        ]:
            if metric in kpis:
                lines.append(f"- {metric}: {kpis[metric]}")

        if alerts:
            lines += ["", "Active alerts:"]
            for a in alerts:
                lines.append(f"- {a['severity'].upper()}: {a['metric']} is {a['condition']} with value {a['value']}")
        else:
            lines += ["", "Active alerts: none detected from current rules."]

        lines += ["", "Recommended actions:"]
        for rec in promo.get("recommendations", []):
            lines.append(f"- {rec}")

        if issues:
            lines += ["", "Strategic playbook:"]
            if persona == "executive":
                lines.append("- Prioritize intervention for stores showing combined sales, inventory, and conversion stress.")
                lines.append("- Reallocate promotion spend toward stores with strong stock health and high show rates.")
            else:
                lines.append("- Execute store-level recovery huddles on conversion blockers, stockouts, and overdue work orders.")
                lines.append("- Push advisor coaching on branded upsell bundles for qualified shoppers.")
            for issue in issues:
                lines.append(f"- {issue['domain']}: {issue['signal']} -> {issue['impact']}")

        lines += ["", "Relevant retrieved context:"]
        for doc in context_docs:
            lines.append(f"- {doc['title']}: {doc['text']}")

        structured_readout = "\n".join(lines)

        if os.environ.get("ANTHROPIC_API_KEY"):
            system_prompt = (
                "You are an AI operations advisor for retail store managers and executives. "
                "Given a structured operational readout with KPIs, alerts, and recommended actions, "
                "produce a concise, actionable narrative summary. "
                "Prioritize clarity and specificity. Use bullet points for actions."
            )
            user_prompt = (
                f"Persona: {persona}\n\n"
                f"Structured readout:\n{structured_readout}\n\n"
                "Generate a concise operational intelligence brief with prioritized actions."
            )
            try:
                return llm_generate(user_prompt, system=system_prompt)
            except Exception as e:
                logger.warning("LLM generation failed, falling back to structured readout: %s", e)

        return structured_readout
