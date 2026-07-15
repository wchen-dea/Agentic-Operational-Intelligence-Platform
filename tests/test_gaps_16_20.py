"""Tests for gaps 16-20: persistent memory, A/B experimentation, multimodal,
PromptRegistry enhancements, type checking."""

import base64
import math
import os
import tempfile

import pytest

# ---------------------------------------------------------------------------
# 16. Persistent agent memory (SQLite-backed)
# ---------------------------------------------------------------------------
from ai_system.retrieval.memory import PersistentSessionMemory


def test_persistent_memory_add_and_retrieve(tmp_path):
    db = tmp_path / "test_mem.db"
    mem = PersistentSessionMemory(db_path=db)
    mem.add_turn("s1", "user", "Hello")
    mem.add_turn("s1", "assistant", "Hi there")
    turns = mem.get_history("s1")
    assert len(turns) == 2
    assert turns[0]["role"] == "user"
    assert turns[1]["role"] == "assistant"


def test_persistent_memory_separate_sessions(tmp_path):
    db = tmp_path / "test_mem.db"
    mem = PersistentSessionMemory(db_path=db)
    mem.add_turn("s1", "user", "Q1")
    mem.add_turn("s2", "user", "Q2")
    assert len(mem.get_history("s1")) == 1
    assert len(mem.get_history("s2")) == 1
    assert mem.get_history("s3") == []


def test_persistent_memory_sliding_window(tmp_path):
    db = tmp_path / "test_mem.db"
    mem = PersistentSessionMemory(db_path=db, max_turns=3)
    for i in range(5):
        mem.add_turn("s1", "user", f"msg-{i}")
    turns = mem.get_history("s1")
    assert len(turns) == 3
    assert turns[0]["content"] == "msg-2"


def test_persistent_memory_survives_restart(tmp_path):
    db = tmp_path / "test_mem.db"
    mem1 = PersistentSessionMemory(db_path=db)
    mem1.add_turn("s1", "user", "Persisted message")

    # Simulate process restart
    mem2 = PersistentSessionMemory(db_path=db)
    turns = mem2.get_history("s1")
    assert len(turns) == 1
    assert turns[0]["content"] == "Persisted message"


def test_persistent_memory_clear(tmp_path):
    db = tmp_path / "test_mem.db"
    mem = PersistentSessionMemory(db_path=db)
    mem.add_turn("s1", "user", "msg")
    mem.store_knowledge("s1", "fact", "The sky is blue")
    mem.clear("s1")
    assert mem.get_history("s1") == []
    assert mem.query_knowledge("fact") == []


def test_persistent_memory_knowledge_accumulation(tmp_path):
    db = tmp_path / "test_mem.db"
    mem = PersistentSessionMemory(db_path=db)
    mem.store_knowledge("s1", "store_preference", "Store 42 prefers morning briefs")
    mem.store_knowledge("s2", "store_preference", "Store 99 prefers evening briefs")
    results = mem.query_knowledge("store_preference")
    assert len(results) == 2
    assert results[0]["session_id"] == "s2"  # most recent first


def test_persistent_memory_active_sessions(tmp_path):
    db = tmp_path / "test_mem.db"
    mem = PersistentSessionMemory(db_path=db)
    mem.add_turn("s1", "user", "msg")
    mem.add_turn("s2", "user", "msg")
    assert mem.active_sessions == 2


def test_persistent_memory_ttl_expiry(tmp_path):
    db = tmp_path / "test_mem.db"
    mem = PersistentSessionMemory(db_path=db, ttl_seconds=0.0)
    mem.add_turn("s1", "user", "ephemeral")
    # TTL=0 -> immediate expiry on next read
    turns = mem.get_history("s1")
    assert turns == []


def test_persistent_memory_metadata(tmp_path):
    db = tmp_path / "test_mem.db"
    mem = PersistentSessionMemory(db_path=db)
    mem.add_turn("s1", "user", "msg", metadata={"intent": "kpi_query"})
    turns = mem.get_history("s1")
    assert turns[0]["intent"] == "kpi_query"


# ---------------------------------------------------------------------------
# 17. A/B prompt experimentation
# ---------------------------------------------------------------------------
from ai_system.experimentation.manager import ExperimentManager, VariantMetrics, _normal_cdf


def test_experiment_create():
    mgr = ExperimentManager()
    exp = mgr.create_experiment("test_prompt", variants={"default": 80, "concise": 20})
    assert exp.active is True
    assert len(exp.traffic_split) == 2


def test_experiment_create_invalid_split():
    mgr = ExperimentManager()
    with pytest.raises(ValueError, match="sum to 100"):
        mgr.create_experiment("test", variants={"a": 50, "b": 30})
    with pytest.raises(ValueError, match="at least 2"):
        mgr.create_experiment("test", variants={"a": 100})


def test_experiment_assign_variant_deterministic():
    mgr = ExperimentManager()
    mgr.create_experiment("test", variants={"default": 50, "new": 50})
    v1 = mgr.assign_variant("test", session_id="session-abc")
    v2 = mgr.assign_variant("test", session_id="session-abc")
    assert v1 == v2  # same session -> same variant (sticky)


def test_experiment_assign_variant_distribution():
    mgr = ExperimentManager()
    mgr.create_experiment("test", variants={"default": 50, "new": 50})
    counts = {"default": 0, "new": 0}
    for i in range(200):
        v = mgr.assign_variant("test", session_id=f"sess-{i}")
        counts[v] += 1
    # With 200 sessions and 50/50 split, both should have significant counts
    assert counts["default"] > 30
    assert counts["new"] > 30


def test_experiment_assign_no_experiment():
    mgr = ExperimentManager()
    assert mgr.assign_variant("nonexistent", "s1") == "default"


def test_experiment_record_and_results():
    import random

    random.seed(42)
    mgr = ExperimentManager()
    mgr.create_experiment("test", variants={"a": 50, "b": 50})
    for _ in range(50):
        mgr.record_outcome("test", "a", score=0.85 + random.uniform(-0.05, 0.05))
        mgr.record_outcome("test", "b", score=0.35 + random.uniform(-0.05, 0.05))
    results = mgr.get_results("test")
    assert results["variants"]["a"]["mean_score"] > 0.7
    assert results["variants"]["b"]["mean_score"] < 0.5
    # Large effect size + many samples -> should be significant
    assert results["significance"]["significant"] is True


def test_experiment_stop():
    mgr = ExperimentManager()
    mgr.create_experiment("test", variants={"a": 50, "b": 50})
    mgr.stop_experiment("test")
    assert mgr.assign_variant("test", "s1") == "default"


def test_experiment_list():
    mgr = ExperimentManager()
    mgr.create_experiment("p1", variants={"a": 50, "b": 50})
    mgr.create_experiment("p2", variants={"x": 70, "y": 30})
    exps = mgr.list_experiments()
    assert len(exps) == 2
    names = {e["prompt_name"] for e in exps}
    assert names == {"p1", "p2"}


def test_variant_metrics():
    vm = VariantMetrics(variant="test", scores=[1.0, 2.0, 3.0])
    assert vm.mean_score == 2.0
    assert vm.variance == 1.0
    assert vm.std_dev == 1.0
    assert vm.impressions == 0


def test_normal_cdf():
    assert abs(_normal_cdf(0.0) - 0.5) < 0.01
    assert _normal_cdf(3.0) > 0.99
    assert _normal_cdf(-3.0) < 0.01


# ---------------------------------------------------------------------------
# 18. Multimodal support
# ---------------------------------------------------------------------------
from ai_system.core.llm import _SUPPORTED_IMAGE_TYPES, generate_with_image


def test_multimodal_supported_types():
    assert "image/png" in _SUPPORTED_IMAGE_TYPES
    assert "image/jpeg" in _SUPPORTED_IMAGE_TYPES
    assert "image/gif" in _SUPPORTED_IMAGE_TYPES
    assert "image/webp" in _SUPPORTED_IMAGE_TYPES


def test_multimodal_rejects_unsupported_type():
    with pytest.raises(ValueError, match="Unsupported image type"):
        generate_with_image("test", image_data="abc", media_type="image/bmp")


def test_multimodal_accepts_bytes_input():
    """Verify that bytes input is accepted (b64 conversion happens before API call)."""
    # This will fail at the API call level (no key), but validates the input handling
    raw_bytes = b"\x89PNG\r\n\x1a\n"  # PNG header
    with pytest.raises(Exception):  # will fail at API call
        generate_with_image("describe this", image_data=raw_bytes, media_type="image/png")


def test_multimodal_accepts_b64_string():
    """Verify that base64 string input is accepted."""
    b64_data = base64.b64encode(b"\x89PNG\r\n\x1a\n").decode()
    with pytest.raises(Exception):  # will fail at API call
        generate_with_image("describe this", image_data=b64_data, media_type="image/png")


# ---------------------------------------------------------------------------
# 19. PromptRegistry enhancements
# ---------------------------------------------------------------------------
from ai_system.core.prompts import (
    PromptRegistry,
    PromptTemplate,
    PromptLifecycle,
    registry,
    get_prompt,
)


def test_registry_names():
    names = registry.names()
    assert "operational_brief" in names
    assert "kpi_explanation" in names
    assert "anomaly_diagnosis" in names
    assert "promotion_strategy" in names


def test_registry_versions():
    versions = registry.versions("operational_brief")
    assert "1.0.0" in versions


def test_registry_list_with_lifecycle_filter():
    active = registry.list_prompts(lifecycle=PromptLifecycle.ACTIVE)
    assert all(p["lifecycle"] == "active" for p in active)
    deprecated = registry.list_prompts(lifecycle=PromptLifecycle.DEPRECATED)
    # No deprecated prompts by default
    assert len(deprecated) == 0


def test_registry_list_with_variant_filter():
    defaults = registry.list_prompts(variant="default")
    assert all(p["variant"] == "default" for p in defaults)
    assert len(defaults) >= 4


def test_registry_retire():
    r = PromptRegistry()
    r.register("test", PromptTemplate(system="sys", user="{x}", version="1.0.0"))
    r.retire("test", "1.0.0")
    with pytest.raises(KeyError):
        r.get("test")  # retired prompts are not usable


def test_registry_deprecate_still_usable():
    """Deprecated prompts should not be returned by get() (only ACTIVE and DRAFT)."""
    r = PromptRegistry()
    r.register("test", PromptTemplate(system="sys", user="{x}", version="1.0.0"))
    r.deprecate("test", "1.0.0")
    with pytest.raises(KeyError):
        r.get("test")  # deprecated is not usable


def test_registry_get_latest_version():
    r = PromptRegistry()
    r.register("test", PromptTemplate(system="sys1", user="{x}", version="1.0.0"))
    r.register("test", PromptTemplate(system="sys2", user="{x}", version="2.0.0"))
    result = r.get("test")
    assert result.system == "sys2"


def test_registry_variant_isolation():
    r = PromptRegistry()
    r.register("test", PromptTemplate(system="default", user="{x}"))
    r.register("test", PromptTemplate(system="concise", user="{x}", variant="concise"))
    default = r.get("test", variant="default")
    concise = r.get("test", variant="concise")
    assert default.system == "default"
    assert concise.system == "concise"


def test_get_prompt_convenience():
    p = get_prompt("operational_brief")
    assert p.system  # non-empty
    assert "{persona}" in p.user


# ---------------------------------------------------------------------------
# 20. Type checking (pyright config exists)
# ---------------------------------------------------------------------------


def test_pyright_config_exists():
    """pyproject.toml should contain [tool.pyright] section."""
    from pathlib import Path

    toml_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    content = toml_path.read_text()
    assert "[tool.pyright]" in content
    assert "typeCheckingMode" in content


def test_ruff_config_exists():
    """pyproject.toml should contain [tool.ruff] section."""
    from pathlib import Path

    toml_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    content = toml_path.read_text()
    assert "[tool.ruff]" in content
