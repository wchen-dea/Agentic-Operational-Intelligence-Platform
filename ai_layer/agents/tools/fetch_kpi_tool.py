"""KPI data access tool - delegates to the queryable data adapter.

The ``data_platform.kpi_store`` module provides a pluggable ``KPIDataSource``
interface.  In development it uses an in-process SQLite database seeded with
sample data; in production it can be swapped to Aurora MySQL or Delta Lake.
"""

from data_platform.kpi_store import fetch_store_kpis  # noqa: F401 - re-exported


# Backward-compatible alias kept so existing callers continue to work.
__all__ = ["fetch_store_kpis"]
