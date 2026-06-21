from typing import Any

from alerts.threshold_config import threshold_min, threshold_max


class PromotionAgent:
    def run(self, kpis: dict[str, Any], context_docs: list[dict[str, Any]]) -> dict[str, Any]:
        low_conversion = kpis.get("appointment_to_order_conversion_rate", 1.0) < threshold_min("appointment_to_order_conversion_rate", 0.25)
        low_show_rate = kpis.get("appointment_show_rate", 1.0) < threshold_min("appointment_show_rate", 0.65)
        high_cycle_time = kpis.get("average_work_order_cycle_time_minutes", 0.0) > threshold_max("average_work_order_cycle_time_minutes", 120)
        low_branded_mix = kpis.get("branded_revenue_mix_rate", 1.0) < threshold_min("branded_revenue_mix_rate", 0.22)
        low_invoice_capture = kpis.get("pos_invoice_capture_rate", 1.0) < threshold_min("pos_invoice_capture_rate", 0.85)
        low_in_stock = kpis.get("inventory_in_stock_rate", 1.0) < threshold_min("inventory_in_stock_rate", 0.90)
        high_stockouts = kpis.get("stockout_sku_count", 0) > threshold_max("stockout_sku_count", 3)

        recommendations = []
        if low_show_rate:
            recommendations.append("Improve appointment reminders and store follow-up before increasing discount depth.")
        if low_conversion:
            recommendations.append("Review promotion messaging and offer clarity for appointment-to-order conversion.")
        if high_cycle_time:
            recommendations.append("Reduce work order backlog before launching demand-heavy promotions.")
        if low_invoice_capture:
            recommendations.append("Investigate POS invoice leakage and checkout friction to protect realized sales and conversion insights.")
        if low_in_stock or high_stockouts:
            recommendations.append("Use inventory-aware promotions: pause campaigns on constrained SKUs and redirect demand to healthy substitutes.")
        if low_branded_mix:
            recommendations.append("Launch branded upsell bundles for high-intent appointments and POS checkouts with manager coaching scripts.")
        if not recommendations:
            recommendations.append("Maintain current promotion strategy and monitor variance by store segment.")

        return {
            "promotion_signal": {
                "low_conversion": low_conversion,
                "low_show_rate": low_show_rate,
                "high_cycle_time": high_cycle_time,
                "low_branded_mix": low_branded_mix,
                "low_invoice_capture": low_invoice_capture,
                "low_inventory_in_stock_rate": low_in_stock,
                "high_stockouts": high_stockouts,
            },
            "recommendations": recommendations,
        }
