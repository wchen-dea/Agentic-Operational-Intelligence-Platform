#!/usr/bin/env bash
# Submit a single canonical PyFlink pipeline to the Flink cluster.
#
# Usage:
#   ./start_flink_job.sh <pipeline_name>
#   ./start_flink_job.sh --list
#
# Examples:
#   ./start_flink_job.sh appointment
#   ./start_flink_job.sh sales_order
#   JOBMANAGER_CONTAINER=my-jobmanager ./start_flink_job.sh vehicle_inspection
#
# Environment variables:
#   JOBMANAGER_CONTAINER  Docker container name/id of the Flink JobManager
#                         (default: agentic-operational-intelligence-platform-flink-jobmanager-1)
#   FLINK_JOBS_DIR        Path to flink_job inside the container
#                         (default: /opt/flink/usrlib/flink_job)

set -euo pipefail

JOBMANAGER_CONTAINER="${JOBMANAGER_CONTAINER:-agentic-operational-intelligence-platform-flink-jobmanager-1}"
FLINK_JOBS_DIR="${FLINK_JOBS_DIR:-/opt/flink/usrlib/flink_job}"
PYFS_ROOT="/opt/flink/usrlib"

AVAILABLE_APPS=(
  appointment
  article
  crewtime
  customer
  employee
  inventory
  kronos_hours
  sales_order
  sales_order_receipt
  site
  vehicle
  vehicle_inspection
  voucher
  work_order
)

# ── --list ────────────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--list" ]]; then
  echo "Available pipelines:"
  for app in "${AVAILABLE_APPS[@]}"; do
    echo "  $app"
  done
  exit 0
fi

# ── Require pipeline name ────────────────────────────────────────────────────
if [[ -z "${1:-}" ]]; then
  echo "Usage: $0 <pipeline_name>"
  echo "       $0 --list"
  exit 1
fi

APP="$1"

# ── Validate pipeline name ────────────────────────────────────────────────────
valid=false
for name in "${AVAILABLE_APPS[@]}"; do
  [[ "$name" == "$APP" ]] && valid=true && break
done
if [[ "$valid" == false ]]; then
  echo "ERROR: Unknown pipeline '$APP'"
  echo "Run '$0 --list' to see available pipelines."
  exit 1
fi

PYTHON_FILE="${FLINK_JOBS_DIR}/${APP}/main.py"

# ── Check the script exists inside the container ─────────────────────────────
if ! docker exec "$JOBMANAGER_CONTAINER" test -f "$PYTHON_FILE"; then
  echo "ERROR: Pipeline script not found in container: $PYTHON_FILE"
  echo "Check that the flink_jobs volume is mounted in $JOBMANAGER_CONTAINER."
  exit 1
fi

# ── Submit ────────────────────────────────────────────────────────────────────
echo "==> Submitting pipeline: $APP"
docker exec "$JOBMANAGER_CONTAINER" \
  /opt/flink/bin/flink run \
    --python  "$PYTHON_FILE" \
    --pyFiles "file://${PYFS_ROOT}" \
    --pyExecutable python3 \
    -d

echo "==> Submitted. Monitor at http://localhost:8082"

