from __future__ import annotations

import logging
import os
from typing import Any

from ai_systems.core.llm import generate as llm_generate
from ai_systems.core.prompts import get_prompt_with_experiment
from ai_systems.alerting.threshold_config import threshold_max, threshold_min
from ai_systems.config.settings import settings

logger = logging.getLogger(__name__)


class RecommendationAgent:
    def diagnose_signals(self, kpis: dict[str, Any], promo: dict[str, Any]) -> list[dict[str, str]]:
        """Analyze KPI and promotion data to identify operational issues."""
        return self._diagnose_signals(kpis, promo)

    def _diagnose_signals(self, kpis: dict[str, Any], promo: dict[str, Any]) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []

        if kpis.get("revenue_total", float("inf")) < threshold_min("revenue_total", 1000):
            issues.append(
                {
                    "domain": "sales_order",
                    "signal": "Low realized sales volume",
                    "impact": "Under-performing store risk and lower daily contribution.",
                }
            )
        if kpis.get("appointment_to_order_conversion_rate", 1.0) < threshold_min(
            "appointment_to_order_conversion_rate", 0.25
        ):
            issues.append(
                {
                    "domain": "appointment",
                    "signal": "Low appointment-to-order conversion",
                    "impact": "Weak conversion funnel and reduced promotion ROI.",
                }
            )
        if kpis.get("pos_invoice_capture_rate", 1.0) < threshold_min("pos_invoice_capture_rate", 0.85):
            issues.append(
                {
                    "domain": "pos_invoice",
                    "signal": "Low POS invoice capture",
                    "impact": "Revenue realization leakage and unreliable downstream KPI analytics.",
                }
            )
        if kpis.get("inventory_in_stock_rate", 1.0) < threshold_min("inventory_in_stock_rate", 0.90) or kpis.get(
            "stockout_sku_count", 0
        ) > threshold_max("stockout_sku_count", 3):
            issues.append(
                {
                    "domain": "inventory",
                    "signal": "Inventory availability pressure",
                    "impact": "Lost upsell opportunities and customer dissatisfaction due to stockouts.",
                }
            )
        if kpis.get("average_work_order_cycle_time_minutes", 0.0) > threshold_max(
            "average_work_order_cycle_time_minutes", 120
        ):
            issues.append(
                {
                    "domain": "work_order",
                    "signal": "Long work-order cycle time",
                    "impact": "Lower same-day fulfillment capacity and weakened conversion confidence.",
                }
            )
        if promo.get("promotion_signal", {}).get("low_branded_mix"):
            issues.append(
                {
                    "domain": "promotion",
                    "signal": "Low branded revenue mix",
                    "impact": "Margin expansion goals are at risk without targeted upsell tactics.",
                }
            )
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
            priority_actions.append(
                {
                    "action": "Rank under-performing stores by revenue, conversion, and stockout pressure for intervention within 24 hours.",
                    "owner": "Regional operations leader",
                    "expected_impact": "Faster diagnosis and tighter cross-store execution.",
                    "time_horizon": "24h",
                }
            )
            priority_actions.append(
                {
                    "action": "Shift campaign budget to stores with healthy in-stock rates and strong appointment show rates.",
                    "owner": "Commercial strategy",
                    "expected_impact": "Higher promotion efficiency and lower wasted spend.",
                    "time_horizon": "This week",
                }
            )
        else:
            priority_actions.append(
                {
                    "action": "Run daily huddles on no-show appointments, overdue work orders, and stockout SKUs.",
                    "owner": "Store manager",
                    "expected_impact": "Improved operational stability and local conversion.",
                    "time_horizon": "Daily",
                }
            )
            priority_actions.append(
                {
                    "action": "Deploy branded upsell scripts for advisors on high-intent appointments and POS checkouts.",
                    "owner": "Store team lead",
                    "expected_impact": "Higher branded mix and improved margin quality.",
                    "time_horizon": "This week",
                }
            )

        for recommendation in promo.get("recommendations", [])[:3]:
            priority_actions.append(
                {
                    "action": recommendation,
                    "owner": "Operations and promotion team",
                    "expected_impact": "Reduced KPI variance and stronger conversion outcomes.",
                    "time_horizon": "1-2 weeks",
                }
            )

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

    # KPIs that are always worth sending (compact set for token efficiency)
    _CORE_KPIS = [
        "revenue_total",
        "order_count",
        "appointment_show_rate",
        "appointment_to_order_conversion_rate",
        "pos_invoice_capture_rate",
        "inventory_in_stock_rate",
        "stockout_sku_count",
        "branded_revenue_mix_rate",
        "average_work_order_cycle_time_minutes",
        "overdue_work_order_count",
    ]

    def _build_compact_readout(
        self,
        kpis: dict[str, Any],
        alerts: list[dict[str, Any]],
        promo: dict[str, Any],
        context_docs: list[dict[str, Any]],
        issues: list[dict[str, str]],
        persona: str,
    ) -> str:
        """Build a token-efficient readout for LLM consumption.

        Optimizations vs full readout:
        - Only includes KPIs that are anomalous or in the core watchlist
        - Limits context docs to top 2 with truncated text
        - Omits verbose playbook text (LLM generates its own)
        """
        store_or_region = kpis.get("store_id") or kpis.get("region") or "scope"
        lines = [f"Readout for {store_or_region} ({persona}):"]

        # Only KPIs that exist and are in the core set
        kpi_lines = [f"  {m}: {kpis[m]}" for m in self._CORE_KPIS if m in kpis]
        if kpi_lines:
            lines.append("KPIs: " + ", ".join(kpi_lines))

        if alerts:
            alert_lines = [
                f"  {a.get('severity', 'medium').upper()}: {a.get('metric')} {a.get('condition')} ({a.get('value')})"
                for a in alerts[:5]  # cap at 5 alerts
            ]
            lines.append("Alerts:" + ", ".join(alert_lines))

        if issues:
            issue_lines = [f"  {i['domain']}: {i['signal']}" for i in issues]
            lines.append("Issues:" + ", ".join(issue_lines))

        recs = promo.get("recommendations", [])[:3]
        if recs:
            lines.append("Actions: " + "; ".join(recs))

        # Top 2 context docs, truncated to 100 chars each
        for doc in context_docs[:2]:
            title = doc.get("title", "")
            text = doc.get("text", "")[:100]
            lines.append(f"Context: {title}: {text}")

        return "\n".join(lines)

    def _build_full_readout(
        self,
        kpis: dict[str, Any],
        alerts: list[dict[str, Any]],
        promo: dict[str, Any],
        context_docs: list[dict[str, Any]],
        issues: list[dict[str, str]],
        persona: str,
    ) -> str:
        """Build the full structured readout (used for non-LLM fallback)."""
        store_or_region = kpis.get("store_id") or kpis.get("region") or "selected scope"
        lines = [f"Operational readout for {store_or_region}:", "", "Key KPI signals:"]

        for metric in self._CORE_KPIS:
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
                lines.append(
                    "- Prioritize intervention for stores showing combined sales, inventory, and conversion stress."
                )
                lines.append("- Reallocate promotion spend toward stores with strong stock health and high show rates.")
            else:
                lines.append(
                    "- Execute store-level recovery huddles on conversion blockers, stockouts, and overdue work orders."
                )
                lines.append("- Push advisor coaching on branded upsell bundles for qualified shoppers.")
            for issue in issues:
                lines.append(f"- {issue['domain']}: {issue['signal']} -> {issue['impact']}")

        lines += ["", "Relevant retrieved context:"]
        for doc in context_docs:
            lines.append(f"- {doc['title']}: {doc['text']}")

        return "\n".join(lines)

    def run(
        self,
        kpis: dict[str, Any],
        alerts: list[dict[str, Any]],
        promo: dict[str, Any],
        context_docs: list[dict[str, Any]],
        persona: str = "store_manager",
        session_id: str | None = None,
    ) -> str:
        issues = self._diagnose_signals(kpis, promo)

        if os.environ.get(settings.llm.api_key_env_var):
            # Resolve prompt via ExperimentManager (sticky variant per session)
            prompt_template, variant = get_prompt_with_experiment("operational_brief", session_id=session_id)
            compact = self._build_compact_readout(kpis, alerts, promo, context_docs, issues, persona)
            user_prompt = prompt_template.format_user(persona=persona, readout=compact)
            try:
                response = llm_generate(
                    user_prompt,
                    system=prompt_template.system,
                    max_tokens=512,
                )
                # Record quality outcome back to ExperimentManager for significance testing
                self._record_experiment_outcome("operational_brief", variant, response, kpis, persona)
                return response
            except Exception as exc:
                logger.warning("LLM generation failed, falling back to structured readout: %s", exc)

        # Fallback: full structured readout (no LLM cost)
        return self._build_full_readout(kpis, alerts, promo, context_docs, issues, persona)

    @staticmethod
    def _record_experiment_outcome(
        prompt_name: str, variant: str, response: str, kpis: dict[str, Any], persona: str
    ) -> None:
        """Compute a quality score and record it for the A/B experiment."""
        try:
            from ai_systems.experimentation.manager import get_experiment_manager
            from observability.evaluation import evaluator

            eval_ctx = {"kpis": kpis, "persona": persona, "question": "", "intent": "operational_brief"}
            results = evaluator.evaluate(response, eval_ctx)
            if results:
                avg_score = sum(r.score for r in results) / len(results)
                get_experiment_manager().record_outcome(prompt_name, variant, avg_score)
        except Exception as exc:
            logger.debug("Could not record experiment outcome: %s", exc)
