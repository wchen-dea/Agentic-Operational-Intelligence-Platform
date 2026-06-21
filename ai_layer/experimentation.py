"""A/B prompt experimentation — traffic splitting, metric collection, and significance testing.

Wires into the existing ``PromptRegistry`` variant support to route a
percentage of traffic to experimental prompt variants, collect per-variant
metrics, and compute statistical significance.

Usage::

    from ai_layer.experimentation import get_experiment_manager

    mgr = get_experiment_manager()
    mgr.create_experiment("kpi_explanation", variants={"default": 80, "concise": 20})
    variant = mgr.assign_variant("kpi_explanation", session_id="sess-123")
    prompt = get_prompt("kpi_explanation", variant=variant)
    # ... generate response ...
    mgr.record_outcome("kpi_explanation", variant, score=0.85)
"""

from __future__ import annotations

import hashlib
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VariantMetrics:
    """Collected metrics for a single prompt variant."""

    variant: str
    impressions: int = 0
    scores: list[float] = field(default_factory=list)

    @property
    def mean_score(self) -> float:
        return sum(self.scores) / len(self.scores) if self.scores else 0.0

    @property
    def variance(self) -> float:
        if len(self.scores) < 2:
            return 0.0
        mean = self.mean_score
        return sum((s - mean) ** 2 for s in self.scores) / (len(self.scores) - 1)

    @property
    def std_dev(self) -> float:
        return math.sqrt(self.variance)


@dataclass
class Experiment:
    """An active A/B experiment on a prompt template."""

    prompt_name: str
    # variant_name → traffic weight (percentages, must sum to 100)
    traffic_split: dict[str, int]
    metrics: dict[str, VariantMetrics] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    active: bool = True

    def __post_init__(self) -> None:
        for variant in self.traffic_split:
            if variant not in self.metrics:
                self.metrics[variant] = VariantMetrics(variant=variant)


class ExperimentManager:
    """Manages A/B prompt experiments with deterministic variant assignment."""

    def __init__(self) -> None:
        self._experiments: dict[str, Experiment] = {}

    def create_experiment(
        self,
        prompt_name: str,
        variants: dict[str, int],
    ) -> Experiment:
        """Create or replace an experiment.

        Args:
            prompt_name: The prompt template name (must match PromptRegistry).
            variants: Mapping of variant name → traffic percentage (must sum to 100).
        """
        total = sum(variants.values())
        if total != 100:
            raise ValueError(f"Traffic split must sum to 100, got {total}")
        if len(variants) < 2:
            raise ValueError("Need at least 2 variants for an experiment")

        exp = Experiment(prompt_name=prompt_name, traffic_split=variants)
        self._experiments[prompt_name] = exp
        logger.info("Created experiment for '%s': %s", prompt_name, variants)
        return exp

    def assign_variant(self, prompt_name: str, session_id: str) -> str:
        """Deterministically assign a session to a variant.

        Uses consistent hashing so the same session always gets the same
        variant (sticky assignment).
        """
        exp = self._experiments.get(prompt_name)
        if exp is None or not exp.active:
            return "default"

        # Consistent hash → bucket (0-99)
        hash_input = f"{prompt_name}:{session_id}"
        bucket = int(hashlib.md5(hash_input.encode()).hexdigest(), 16) % 100

        cumulative = 0
        for variant, weight in exp.traffic_split.items():
            cumulative += weight
            if bucket < cumulative:
                exp.metrics[variant].impressions += 1
                return variant

        # Fallback (shouldn't happen if weights sum to 100)
        return "default"

    def record_outcome(
        self,
        prompt_name: str,
        variant: str,
        score: float,
    ) -> None:
        """Record a quality score for a variant impression."""
        exp = self._experiments.get(prompt_name)
        if exp is None:
            return
        metrics = exp.metrics.get(variant)
        if metrics is not None:
            metrics.scores.append(score)

    def get_results(self, prompt_name: str) -> dict[str, Any]:
        """Return experiment results with optional significance test."""
        exp = self._experiments.get(prompt_name)
        if exp is None:
            return {"error": f"No experiment for '{prompt_name}'"}

        result: dict[str, Any] = {
            "prompt_name": prompt_name,
            "active": exp.active,
            "variants": {},
        }

        for variant, metrics in exp.metrics.items():
            result["variants"][variant] = {
                "impressions": metrics.impressions,
                "scores_collected": len(metrics.scores),
                "mean_score": round(metrics.mean_score, 4),
                "std_dev": round(metrics.std_dev, 4),
                "traffic_pct": exp.traffic_split.get(variant, 0),
            }

        # Statistical significance (Welch's t-test between first two variants)
        variant_names = list(exp.metrics.keys())
        if len(variant_names) >= 2:
            sig = self._welch_t_test(
                exp.metrics[variant_names[0]],
                exp.metrics[variant_names[1]],
            )
            result["significance"] = sig

        return result

    def stop_experiment(self, prompt_name: str) -> None:
        """Deactivate an experiment (all traffic goes to default)."""
        exp = self._experiments.get(prompt_name)
        if exp:
            exp.active = False
            logger.info("Stopped experiment for '%s'", prompt_name)

    def list_experiments(self) -> list[dict[str, Any]]:
        """List all experiments with summary info."""
        return [
            {
                "prompt_name": exp.prompt_name,
                "active": exp.active,
                "variants": list(exp.traffic_split.keys()),
                "total_impressions": sum(m.impressions for m in exp.metrics.values()),
            }
            for exp in self._experiments.values()
        ]

    @staticmethod
    def _welch_t_test(a: VariantMetrics, b: VariantMetrics) -> dict[str, Any]:
        """Welch's t-test for unequal variances between two variants."""
        n_a, n_b = len(a.scores), len(b.scores)
        if n_a < 2 or n_b < 2:
            return {"significant": False, "reason": "insufficient_data", "min_samples": 2}

        mean_a, mean_b = a.mean_score, b.mean_score
        var_a, var_b = a.variance, b.variance

        se = math.sqrt(var_a / n_a + var_b / n_b)
        if se == 0:
            return {"significant": False, "reason": "zero_variance"}

        t_stat = (mean_a - mean_b) / se

        # Welch-Satterthwaite degrees of freedom
        num = (var_a / n_a + var_b / n_b) ** 2
        denom = (var_a / n_a) ** 2 / (n_a - 1) + (var_b / n_b) ** 2 / (n_b - 1)
        df = num / denom if denom > 0 else 1.0

        # Approximate p-value using normal distribution for large df
        # (avoids scipy dependency)
        z = abs(t_stat)
        # Abramowitz & Stegun approximation for Phi(z)
        p_approx = 2.0 * (1.0 - _normal_cdf(z))

        return {
            "significant": p_approx < 0.05,
            "t_statistic": round(t_stat, 4),
            "degrees_of_freedom": round(df, 2),
            "p_value_approx": round(p_approx, 4),
            "mean_a": round(mean_a, 4),
            "mean_b": round(mean_b, 4),
            "n_a": n_a,
            "n_b": n_b,
        }


def _normal_cdf(z: float) -> float:
    """Standard normal CDF approximation (Abramowitz & Stegun 26.2.17)."""
    if z < 0:
        return 1.0 - _normal_cdf(-z)
    b0 = 0.2316419
    b1 = 0.319381530
    b2 = -0.356563782
    b3 = 1.781477937
    b4 = -1.821255978
    b5 = 1.330274429
    t = 1.0 / (1.0 + b0 * z)
    phi = 1.0 - (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-z * z / 2.0) * (
        b1 * t + b2 * t**2 + b3 * t**3 + b4 * t**4 + b5 * t**5
    )
    return phi


# Singleton
_manager: ExperimentManager | None = None


def get_experiment_manager() -> ExperimentManager:
    global _manager
    if _manager is None:
        _manager = ExperimentManager()
    return _manager
