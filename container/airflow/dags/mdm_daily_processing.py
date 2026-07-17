"""DAG: mdm_daily_processing

Runs a single daily master-data batch publish to canonical Kafka topics.

Schedule : daily at 02:00 UTC
Catchup  : disabled
Retries  : 2 per task (with 5-minute delay)
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

DEFAULT_ARGS = {
    "owner": "data-platform",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=1),
}

DEFAULT_BATCH_SIZE = os.environ.get("MDM_BATCH_SIZE", "500")
DEFAULT_KAFKA_BROKERS = os.environ.get(
    "MDM_KAFKA_BROKERS",
    os.environ.get("KAFKA_BROKERS", "host.docker.internal:9092"),
)
DEFAULT_SCHEMA_REGISTRY = os.environ.get(
    "MDM_SCHEMA_REGISTRY_URL",
    os.environ.get("SCHEMA_REGISTRY_URL", "http://host.docker.internal:8081"),
)


@dag(
    dag_id="mdm_daily_processing",
    description="Daily MDM batch producer for master data topics",
    schedule="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["kafka", "producer", "mdm"],
)
def mdm_daily_processing():
    start = EmptyOperator(task_id="start")

    run_mdm_batch = BashOperator(
        task_id="run_mdm_batch",
        bash_command=(
            "set -euo pipefail; "
            "cd /opt/airflow; "
            "export PYTHONPATH=/opt/airflow:${PYTHONPATH:-}; "
            "python -m data_platform.producer.mdm.master_batch "
            "--runs 1 "
            "--batch-size {{ dag_run.conf.get('batch_size', params.batch_size) }} "
            "--brokers {{ dag_run.conf.get('brokers', params.brokers) }} "
            "--schema-registry {{ dag_run.conf.get('schema_registry', params.schema_registry) }} "
            "--interval-seconds 0"
        ),
        params={
            "batch_size": DEFAULT_BATCH_SIZE,
            "brokers": DEFAULT_KAFKA_BROKERS,
            "schema_registry": DEFAULT_SCHEMA_REGISTRY,
        },
    )

    end = EmptyOperator(task_id="end")

    start >> run_mdm_batch >> end


mdm_daily_processing()
