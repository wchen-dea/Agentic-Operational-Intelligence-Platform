"""Centralized prompt registry with versioning and lifecycle management.

All prompts used across the platform are defined here to ensure consistency,
ease of tuning, and single-source-of-truth management.

LLMOps features:
- Semantic versioning per prompt template
- Lifecycle states (draft → active → deprecated → retired)
- A/B variant support for prompt experimentation
- Programmatic lookup by name + version
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PromptLifecycle(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass(frozen=True)
class PromptTemplate:
    """A versioned, paired system + user prompt template."""

    system: str
    user: str
    version: str = "1.0.0"
    lifecycle: PromptLifecycle = PromptLifecycle.ACTIVE
    variant: str = "default"
    metadata: dict[str, Any] = field(default_factory=dict)

    def format_user(self, **kwargs: str) -> str:
        """Render the user template with the given variables."""
        return self.user.format(**kwargs)

    @property
    def is_usable(self) -> bool:
        return self.lifecycle in (PromptLifecycle.ACTIVE, PromptLifecycle.DRAFT)


# ---------------------------------------------------------------------------
# Operational Intelligence Prompts
# ---------------------------------------------------------------------------

OPERATIONAL_BRIEF = PromptTemplate(
    system=(
        "You are an AI operations advisor for retail store managers and executives. "
        "Given a structured operational readout with KPIs, alerts, and recommended actions, "
        "produce a concise, actionable narrative summary. "
        "Prioritize clarity and specificity. Use bullet points for actions. "
        "Tailor depth and language to the specified persona."
    ),
    user=(
        "Persona: {persona}\n\n"
        "Structured readout:\n{readout}\n\n"
        "Generate a concise operational intelligence brief with prioritized actions."
    ),
    version="1.0.0",
    lifecycle=PromptLifecycle.ACTIVE,
)

KPI_EXPLANATION = PromptTemplate(
    system=(
        "You are an AI retail operations analyst. "
        "Explain the operational KPI issue using: "
        "1. Current metrics 2. Alerts 3. Retrieved business context "
        "4. Likely causes 5. Recommended actions. "
        "Keep the response executive-ready and concise."
    ),
    user=(
        "Persona: {persona}\n\n"
        "KPIs:\n{kpis}\n\n"
        "Alerts:\n{alerts}\n\n"
        "Context:\n{context}\n\n"
        "Explain what is happening and what to do about it."
    ),
    version="1.0.0",
    lifecycle=PromptLifecycle.ACTIVE,
)

ANOMALY_DIAGNOSIS = PromptTemplate(
    system=(
        "You are an AI anomaly diagnosis specialist for retail operations. "
        "Given threshold breaches and KPI data, explain the root cause, "
        "business impact, and immediate corrective actions. "
        "Be specific and action-oriented."
    ),
    user=(
        "Persona: {persona}\n\n"
        "Breached alerts:\n{alerts}\n\n"
        "Current KPIs:\n{kpis}\n\n"
        "Diagnose the anomalies and recommend corrective actions."
    ),
    version="1.0.0",
    lifecycle=PromptLifecycle.ACTIVE,
)

PROMOTION_STRATEGY = PromptTemplate(
    system=(
        "You are an AI promotion strategy advisor for retail operations. "
        "Analyze promotion effectiveness signals and recommend adjustments. "
        "Consider inventory health, conversion rates, and margin impact. "
        "Provide concrete, store-level actionable recommendations."
    ),
    user=(
        "Persona: {persona}\n\n"
        "Promotion signals:\n{signals}\n\n"
        "Current KPIs:\n{kpis}\n\n"
        "Recommend promotion strategy adjustments."
    ),
    version="1.0.0",
    lifecycle=PromptLifecycle.ACTIVE,
)

# ---------------------------------------------------------------------------
# Versioned registry with variant support
# ---------------------------------------------------------------------------


class PromptRegistry:
    """Manages prompt templates with versioning, lifecycle, and A/B variant selection.

    Full runtime API:
    - ``register(name, template)`` — add a prompt
    - ``get(name, version, variant)`` — retrieve by name (latest active if no version)
    - ``deprecate(name, version, variant)`` — mark a version deprecated
    - ``retire(name, version, variant)`` — mark a version retired (hidden from ``get()``)
    - ``list_prompts(**filters)`` — list with optional lifecycle/variant filters
    - ``names()`` — unique prompt names
    - ``versions(name)`` — versions available for a prompt
    """

    def __init__(self) -> None:
        # key: (name, version, variant)
        self._store: dict[tuple[str, str, str], PromptTemplate] = {}

    def register(self, name: str, template: PromptTemplate) -> None:
        key = (name, template.version, template.variant)
        self._store[key] = template

    def get(
        self,
        name: str,
        version: str | None = None,
        variant: str = "default",
    ) -> PromptTemplate:
        """Retrieve a prompt by name. If version is None, returns the latest active version."""
        if version:
            key = (name, version, variant)
            if key not in self._store:
                raise KeyError(f"Prompt '{name}' v{version} variant='{variant}' not found.")
            return self._store[key]

        # Find latest active version for this name + variant
        candidates = [
            (k, t) for k, t in self._store.items()
            if k[0] == name and k[2] == variant and t.is_usable
        ]
        if not candidates:
            raise KeyError(f"No active prompt found for '{name}' variant='{variant}'.")
        # Sort by version descending (semantic)
        candidates.sort(key=lambda x: _version_tuple(x[0][1]), reverse=True)
        return candidates[0][1]

    def list_prompts(
        self,
        lifecycle: PromptLifecycle | None = None,
        variant: str | None = None,
    ) -> list[dict[str, str]]:
        """List registered prompts with optional lifecycle/variant filters."""
        results = []
        for k, t in sorted(self._store.items()):
            if lifecycle is not None and t.lifecycle != lifecycle:
                continue
            if variant is not None and k[2] != variant:
                continue
            results.append({
                "name": k[0], "version": k[1], "variant": k[2], "lifecycle": t.lifecycle.value,
            })
        return results

    def names(self) -> list[str]:
        """Return unique prompt names."""
        return sorted({k[0] for k in self._store})

    def versions(self, name: str) -> list[str]:
        """Return all versions registered for a prompt name."""
        return sorted(
            {k[1] for k in self._store if k[0] == name},
            key=_version_tuple,
            reverse=True,
        )

    def deprecate(self, name: str, version: str, variant: str = "default") -> None:
        """Mark a prompt version as deprecated."""
        self._set_lifecycle(name, version, variant, PromptLifecycle.DEPRECATED)

    def retire(self, name: str, version: str, variant: str = "default") -> None:
        """Mark a prompt version as retired (excluded from ``get()`` lookup)."""
        self._set_lifecycle(name, version, variant, PromptLifecycle.RETIRED)

    def _set_lifecycle(
        self, name: str, version: str, variant: str, lifecycle: PromptLifecycle,
    ) -> None:
        key = (name, version, variant)
        if key not in self._store:
            raise KeyError(f"Prompt '{name}' v{version} variant='{variant}' not found.")
        old = self._store[key]
        self._store[key] = PromptTemplate(
            system=old.system,
            user=old.user,
            version=old.version,
            lifecycle=lifecycle,
            variant=old.variant,
            metadata=old.metadata,
        )


def _version_tuple(version: str) -> tuple[int, ...]:
    """Parse semver string into comparable tuple."""
    parts = []
    for p in version.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


# ---------------------------------------------------------------------------
# Default registry instance (pre-loaded with all prompts)
# ---------------------------------------------------------------------------

registry = PromptRegistry()
registry.register("operational_brief", OPERATIONAL_BRIEF)
registry.register("kpi_explanation", KPI_EXPLANATION)
registry.register("anomaly_diagnosis", ANOMALY_DIAGNOSIS)
registry.register("promotion_strategy", PROMOTION_STRATEGY)


def get_prompt(name: str, version: str | None = None, variant: str = "default") -> PromptTemplate:
    """Retrieve a prompt template by name (with optional version/variant)."""
    return registry.get(name, version=version, variant=variant)
