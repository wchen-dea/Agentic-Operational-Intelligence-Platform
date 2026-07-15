"""Guardrails - input validation, output validation, and content safety.

Provides three layers of protection:
1. **Input guardrails** - prompt injection detection, PII scrubbing, length limits
2. **Output guardrails** - hallucination checks, schema conformance, content filtering
3. **FastAPI middleware** - wraps every request/response through the guardrail pipeline
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class GuardrailAction(str, Enum):
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""

    action: GuardrailAction = GuardrailAction.PASS
    checks: list[dict[str, Any]] = field(default_factory=list)
    sanitized_text: str | None = None

    @property
    def passed(self) -> bool:
        return self.action != GuardrailAction.BLOCK


# ---------------------------------------------------------------------------
# Input guardrails
# ---------------------------------------------------------------------------

# Patterns commonly used in prompt injection attacks
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)", re.I),
    re.compile(r"you\s+are\s+now\s+(a|an|the)\s+", re.I),
    re.compile(r"system\s*:\s*", re.I),
    re.compile(r"<\s*/?\s*system\s*>", re.I),
    re.compile(r"do\s+not\s+follow\s+(your|the)\s+(instructions?|rules?|guidelines?)", re.I),
    re.compile(r"override\s+(your|the|all)\s+(safety|content|system)", re.I),
    re.compile(r"pretend\s+(you\s+are|to\s+be)\s+", re.I),
    re.compile(r"\bDAN\b.*\bjailbreak\b", re.I),
]

# PII patterns for scrubbing
_PII_PATTERNS = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "email": re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
}

_MAX_INPUT_LENGTH = 10_000  # characters


def validate_input(text: str, scrub_pii: bool = True) -> GuardrailResult:
    """Validate user input for safety before sending to the LLM.

    Checks for:
    - Prompt injection patterns
    - PII (optionally scrubbed)
    - Input length limits
    """
    checks: list[dict[str, Any]] = []
    action = GuardrailAction.PASS
    sanitized = text

    # Length check
    if len(text) > _MAX_INPUT_LENGTH:
        checks.append(
            {
                "check": "input_length",
                "status": "blocked",
                "detail": f"Input exceeds {_MAX_INPUT_LENGTH} characters ({len(text)}).",
            }
        )
        action = GuardrailAction.BLOCK
        return GuardrailResult(action=action, checks=checks, sanitized_text=None)
    checks.append({"check": "input_length", "status": "pass"})

    # Prompt injection detection
    injection_matches = []
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            injection_matches.append(match.group())
    if injection_matches:
        checks.append(
            {
                "check": "prompt_injection",
                "status": "blocked",
                "detail": f"Detected {len(injection_matches)} prompt injection pattern(s).",
                "matches": injection_matches,
            }
        )
        action = GuardrailAction.BLOCK
        return GuardrailResult(action=action, checks=checks, sanitized_text=None)
    checks.append({"check": "prompt_injection", "status": "pass"})

    # PII detection and scrubbing
    pii_found: list[str] = []
    for pii_type, pattern in _PII_PATTERNS.items():
        if pattern.search(sanitized):
            pii_found.append(pii_type)
            if scrub_pii:
                sanitized = pattern.sub(f"[{pii_type.upper()}_REDACTED]", sanitized)
    if pii_found:
        checks.append(
            {
                "check": "pii_detection",
                "status": "warn" if scrub_pii else "blocked",
                "detail": f"Detected PII types: {', '.join(pii_found)}.",
                "scrubbed": scrub_pii,
            }
        )
        if not scrub_pii:
            action = GuardrailAction.BLOCK
        else:
            action = max(action, GuardrailAction.WARN, key=lambda x: list(GuardrailAction).index(x))
    else:
        checks.append({"check": "pii_detection", "status": "pass"})

    return GuardrailResult(action=action, checks=checks, sanitized_text=sanitized)


# ---------------------------------------------------------------------------
# Output guardrails
# ---------------------------------------------------------------------------

# Words/phrases that should never appear in operational advice
_BLOCKED_OUTPUT_PATTERNS = [
    re.compile(r"\b(password|secret|api[_\s]?key|credentials?)\b.*\b(is|are|was)\b.*\b\S{8,}\b", re.I),
]


def validate_output(
    text: str,
    kpi_names: list[str] | None = None,
) -> GuardrailResult:
    """Validate LLM output before returning to the user.

    Checks for:
    - Blocked content patterns (credential leakage)
    - Hallucination signal: fabricated KPI names not in the known catalog
    - Response quality: minimum length
    """
    checks: list[dict[str, Any]] = []
    action = GuardrailAction.PASS

    # Blocked output patterns
    for pattern in _BLOCKED_OUTPUT_PATTERNS:
        if pattern.search(text):
            checks.append(
                {
                    "check": "blocked_content",
                    "status": "blocked",
                    "detail": "Output contains potentially sensitive content.",
                }
            )
            action = GuardrailAction.BLOCK
            return GuardrailResult(action=action, checks=checks)
    checks.append({"check": "blocked_content", "status": "pass"})

    # Hallucination check - look for metric names that don't exist in catalog
    if kpi_names:
        # Extract metric-like names from the output (snake_case words)
        mentioned = set(re.findall(r"\b([a-z][a-z0-9_]{5,})\b", text.lower()))
        known = set(k.lower() for k in kpi_names)
        # Only flag terms that look like KPI names (contain common suffixes)
        kpi_suffixes = {"_rate", "_count", "_total", "_time", "_pct", "_proxy", "_mix"}
        fabricated = {m for m in mentioned - known if any(m.endswith(s) for s in kpi_suffixes)}
        if fabricated:
            checks.append(
                {
                    "check": "hallucination",
                    "status": "warn",
                    "detail": f"Potentially fabricated KPI names: {', '.join(sorted(fabricated))}.",
                }
            )
            action = max(action, GuardrailAction.WARN, key=lambda x: list(GuardrailAction).index(x))
        else:
            checks.append({"check": "hallucination", "status": "pass"})

    # Minimum quality
    word_count = len(text.split())
    if word_count < 5:
        checks.append(
            {
                "check": "quality",
                "status": "warn",
                "detail": f"Output is very short ({word_count} words).",
            }
        )
        action = max(action, GuardrailAction.WARN, key=lambda x: list(GuardrailAction).index(x))
    else:
        checks.append({"check": "quality", "status": "pass"})

    return GuardrailResult(action=action, checks=checks, sanitized_text=text)
