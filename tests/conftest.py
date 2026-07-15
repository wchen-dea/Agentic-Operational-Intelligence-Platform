"""
Pytest configuration — applies environment overrides before any application
module is imported so the test suite is fully self-contained.

Overrides (test-only):
  AOIP_AUTH_DISABLED=true   — disables API key auth so tests hit endpoints directly
  AOIP_KPI_SOURCE=sqlite    — uses the bundled SQLite fixture, no MySQL/pymysql needed
"""
import os

# Must be set before any app import
os.environ.setdefault("AOIP_AUTH_DISABLED", "true")
os.environ.setdefault("AOIP_KPI_SOURCE", "sqlite")
