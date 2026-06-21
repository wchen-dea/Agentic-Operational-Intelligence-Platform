"""Tests for the AI-ready data layer: semantic KPIs, SQLite adapter, and KPI catalog."""

from data_platform.semantic_layer import (
    DataProvenance,
    KPIRecord,
    StoreKPISnapshot,
    enrich_kpis,
    get_kpi_metadata,
)
from data_platform.kpi_store import SQLiteKPISource, fetch_store_kpis


# ---------------------------------------------------------------------------
# KPI catalog
# ---------------------------------------------------------------------------

def test_kpi_catalog_loads():
    meta = get_kpi_metadata("revenue_total")
    assert meta["unit"] == "USD"
    assert meta["direction"] == "higher_is_better"
    assert meta["domain"] == "sales_order"
    assert "description" in meta


def test_kpi_catalog_unknown_metric():
    meta = get_kpi_metadata("nonexistent_metric_xyz")
    assert meta == {}


# ---------------------------------------------------------------------------
# KPIRecord
# ---------------------------------------------------------------------------

def test_kpi_record_anomalous_below_min():
    r = KPIRecord(name="revenue_total", value=500.0, threshold_min=1000.0)
    assert r.is_anomalous is True


def test_kpi_record_anomalous_above_max():
    r = KPIRecord(name="stockout_sku_count", value=10.0, threshold_max=3.0)
    assert r.is_anomalous is True


def test_kpi_record_ok():
    r = KPIRecord(name="revenue_total", value=2000.0, threshold_min=1000.0)
    assert r.is_anomalous is False


def test_kpi_record_to_llm_summary():
    r = KPIRecord(
        name="revenue_total", value=500.0, unit="USD",
        threshold_min=1000.0, description="Total revenue.",
    )
    summary = r.to_llm_summary()
    assert "ANOMALOUS" in summary
    assert "500.0" in summary
    assert "USD" in summary


# ---------------------------------------------------------------------------
# DataProvenance
# ---------------------------------------------------------------------------

def test_data_provenance_to_dict():
    prov = DataProvenance(source="sqlite", event_count=42)
    d = prov.to_dict()
    assert d["source"] == "sqlite"
    assert d["event_count"] == 42
    assert isinstance(d["computed_at"], float)


# ---------------------------------------------------------------------------
# enrich_kpis
# ---------------------------------------------------------------------------

def test_enrich_kpis_from_raw():
    raw = {
        "store_id": "245",
        "region": "Phoenix",
        "revenue_total": 820.0,
        "appointment_show_rate": 0.58,
        "stockout_sku_count": 6,
    }
    snapshot = enrich_kpis(raw)
    assert isinstance(snapshot, StoreKPISnapshot)
    assert snapshot.store_id == "245"
    assert len(snapshot.records) == 3

    # Revenue should be anomalous (820 < 1000 threshold)
    rev = next(r for r in snapshot.records if r.name == "revenue_total")
    assert rev.is_anomalous is True
    assert rev.unit == "USD"

    # Stockout should be anomalous (6 > 3 threshold)
    stock = next(r for r in snapshot.records if r.name == "stockout_sku_count")
    assert stock.is_anomalous is True

    assert len(snapshot.anomalous_records) >= 2


def test_enrich_kpis_flat_dict_roundtrip():
    raw = {"store_id": "101", "revenue_total": 4300.0, "order_count": 41}
    snapshot = enrich_kpis(raw)
    flat = snapshot.to_flat_dict()
    assert flat["store_id"] == "101"
    assert flat["revenue_total"] == 4300.0
    assert flat["order_count"] == 41


def test_enrich_kpis_llm_context():
    raw = {"store_id": "245", "revenue_total": 820.0}
    snapshot = enrich_kpis(raw)
    ctx = snapshot.to_llm_context()
    assert "Store 245" in ctx
    assert "revenue_total" in ctx


# ---------------------------------------------------------------------------
# SQLiteKPISource
# ---------------------------------------------------------------------------

def test_sqlite_source_fetch_by_store():
    src = SQLiteKPISource()  # in-memory, seeded
    data = src.fetch_by_store("245")
    assert data["store_id"] == "245"
    assert data["revenue_total"] == 820.0


def test_sqlite_source_fetch_by_region():
    src = SQLiteKPISource()
    data = src.fetch_by_region("Phoenix")
    assert data["region"] == "Phoenix"
    assert data["store_count"] == 2
    assert data["revenue_total"] == 820.0 + 4300.0


def test_sqlite_source_fetch_all():
    src = SQLiteKPISource()
    rows = src.fetch_all()
    assert len(rows) == 2
    store_ids = {r["store_id"] for r in rows}
    assert store_ids == {"245", "101"}


def test_sqlite_source_upsert():
    src = SQLiteKPISource()
    src.upsert("999", {"region": "Dallas", "revenue_total": 5000.0, "order_count": 50})
    data = src.fetch_by_store("999")
    assert data["store_id"] == "999"
    assert data["revenue_total"] == 5000.0


def test_sqlite_source_missing_store():
    src = SQLiteKPISource()
    data = src.fetch_by_store("nonexistent")
    assert data == {}


# ---------------------------------------------------------------------------
# fetch_store_kpis (high-level function)
# ---------------------------------------------------------------------------

def test_fetch_store_kpis_backward_compatible():
    data = fetch_store_kpis(store_id="245")
    assert data["store_id"] == "245"
    assert "revenue_total" in data


def test_fetch_store_kpis_enriched():
    snapshot = fetch_store_kpis(store_id="245", enrich=True)
    assert isinstance(snapshot, StoreKPISnapshot)
    assert snapshot.store_id == "245"
    assert any(r.name == "revenue_total" for r in snapshot.records)


def test_fetch_store_kpis_region():
    data = fetch_store_kpis(region="Phoenix")
    assert data["region"] == "Phoenix"
    assert "appointment_show_rate" in data
