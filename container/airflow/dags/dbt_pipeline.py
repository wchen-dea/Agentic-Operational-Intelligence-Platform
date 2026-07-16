"""
DAG: dbt_lakehouse_pipeline
============================
Orchestrates the full dbt medallion pipeline on the Iceberg lakehouse:

  1. dbt deps         — install / refresh dbt packages
  2. dbt run (bronze) — CDC envelope flattening, append-only
  3. dbt test (bronze)— data quality gate before promoting to silver
  4. dbt run (silver) — CDC merge to current-state tables
  5. dbt test (silver)— data quality gate before building gold
  6. dbt run (gold)   — KPI aggregation tables
  7. dbt test (gold)  — final quality check

Schedule : every 30 minutes (configurable via DAG params)
Catchup  : disabled
Retries  : 2 per task (with 5-minute delay)

Environment variables consumed:
    DBT_PROJECT_DIR   path to dbt project inside the container (default: /opt/airflow/dbt)
    DBT_PROFILES_DIR  path to profiles.yml                     (default: /opt/airflow/dbt)
    DBT_TARGET        dbt target (default: dev)
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow.decorators import dag, task_group
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DBT_PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/opt/airflow/dbt")
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", "/opt/airflow/dbt")
DBT_TARGET = os.environ.get("DBT_TARGET", "dev")

DBT_BASE_CMD = (
    f"dbt {{command}} --project-dir {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR} --target {DBT_TARGET} {{extra}}"
)


def dbt_cmd(command: str, select: str | None = None, extra: str = "") -> str:
    sel = f"--select {select}" if select else ""
    return DBT_BASE_CMD.format(command=command, extra=f"{sel} {extra}".strip())


# ---------------------------------------------------------------------------
# Default task arguments
# ---------------------------------------------------------------------------
DEFAULT_ARGS = {
    "owner": "data-platform",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=30),
}


@dag(
    dag_id="dbt_lakehouse_pipeline",
    description="dbt bronze → silver → gold Iceberg lakehouse pipeline",
    schedule="*/30 * * * *",  # every 30 minutes
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["dbt", "iceberg", "lakehouse"],
    params={
        "full_refresh": False,
    },
)
def dbt_lakehouse_pipeline():

    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    # ── 1. Package installation ───────────────────────────────────────────
    deps = BashOperator(
        task_id="dbt_deps",
        bash_command=dbt_cmd("deps"),
    )

    # ── 2. Bronze layer ───────────────────────────────────────────────────
    @task_group(group_id="bronze")
    def bronze_group():
        run = BashOperator(
            task_id="run",
            bash_command=dbt_cmd(
                "run",
                select="+bronze",
                extra="{{ '--full-refresh' if params.full_refresh else '' }}",
            ),
        )
        test = BashOperator(
            task_id="test",
            bash_command=dbt_cmd("test", select="bronze"),
        )
        run >> test

    # ── 3. Silver layer ───────────────────────────────────────────────────
    @task_group(group_id="silver")
    def silver_group():
        run = BashOperator(
            task_id="run",
            bash_command=dbt_cmd(
                "run",
                select="silver",
                extra="{{ '--full-refresh' if params.full_refresh else '' }}",
            ),
        )
        test = BashOperator(
            task_id="test",
            bash_command=dbt_cmd("test", select="silver"),
        )
        run >> test

    # ── 4. Gold layer ─────────────────────────────────────────────────────
    @task_group(group_id="gold")
    def gold_group():
        run = BashOperator(
            task_id="run",
            bash_command=dbt_cmd("run", select="gold"),
        )
        test = BashOperator(
            task_id="test",
            bash_command=dbt_cmd("test", select="gold"),
        )
        run >> test

    # ── DAG wiring ────────────────────────────────────────────────────────
    b = bronze_group()
    s = silver_group()
    g = gold_group()

    start >> deps >> b >> s >> g >> end


dbt_lakehouse_pipeline()
