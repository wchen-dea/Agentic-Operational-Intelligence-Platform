"""
Feature materialization script — pushes analytics layer features to Redis.

Run on-demand or schedule via Airflow after each dbt analytics run.

Usage
─────
    # Materialize everything from epoch to now (first time)
    python materialize.py --full

    # Incremental: materialize new records since last watermark
    python materialize.py
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("feast.materialize")

FEAST_REPO_PATH = os.path.dirname(__file__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Feast feature materialization")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full materialization from epoch (use on first run)",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="End date for materialization (ISO-8601, default: now)",
    )
    args = parser.parse_args()

    try:
        from feast import FeatureStore
    except ImportError:
        logger.error("feast is not installed. Run: pip install feast[spark,redis]")
        sys.exit(1)

    store = FeatureStore(repo_path=FEAST_REPO_PATH)
    end_date = datetime.fromisoformat(args.end_date) if args.end_date else datetime.now(tz=timezone.utc)

    if args.full:
        from datetime import timedelta

        start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        logger.info("Full materialization: %s → %s", start_date.date(), end_date.date())
        store.materialize(start_date=start_date, end_date=end_date)
    else:
        logger.info("Incremental materialization up to: %s", end_date.isoformat())
        store.materialize_incremental(end_date=end_date)

    logger.info("Materialization complete. Features available in Redis.")


if __name__ == "__main__":
    main()
