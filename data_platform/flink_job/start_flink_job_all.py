"""Submit all canonical PyFlink pipelines to the Flink cluster in one shot.

Loops through every pipeline in order and calls start_flink_job.sh (or the
equivalent docker exec flink run) for each one.

Usage
-----
    python start_flink_job_all.py
    python start_flink_job_all.py --dry-run
    python start_flink_job_all.py --list

Environment variables
---------------------
    JOBMANAGER_CONTAINER  Docker container name of the Flink JobManager
                          (default: agentic-operational-intelligence-platform-flink-jobmanager-1)
    FLINK_JOBS_DIR        Path inside the container to the flink_job directory
                          (default: /opt/flink/usrlib/flink_job)
    PYFS_ROOT             --pyFiles root passed to flink run
                          (default: /opt/flink/usrlib)
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("flink.submit_all")

PIPELINES: list[str] = [
    "appointment",
    "article",
    "crewtime",
    "customer",
    "employee",
    "inventory",
    "kronos_hours",
    "sales_order",
    "sales_order_receipt",
    "site",
    "vehicle",
    "vehicle_inspection",
    "voucher",
    "work_order",
]


def _submit(pipeline: str, *, jobmanager: str, jobs_dir: str, pyfs_root: str, dry_run: bool) -> bool:
    python_file = f"{jobs_dir}/{pipeline}/main.py"
    cmd = [
        "docker",
        "exec",
        jobmanager,
        "/opt/flink/bin/flink",
        "run",
        "--python",
        python_file,
        "--pyFiles",
        f"file://{pyfs_root}",
        "--pyExecutable",
        "python3",
        "-d",
    ]

    if dry_run:
        logger.info("[dry-run] %s", " ".join(cmd))
        return True

    logger.info("==> Submitting: %s", pipeline)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        logger.info("    OK  %s", pipeline)
        return True
    else:
        logger.error("    FAILED  %s\n%s", pipeline, result.stderr.strip())
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Submit all canonical PyFlink pipelines to the Flink cluster.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print pipeline names and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them",
    )
    args = parser.parse_args()

    if args.list:
        print("Pipelines to be submitted:")
        for name in PIPELINES:
            print(f"  {name}")
        sys.exit(0)

    jobmanager = os.environ.get(
        "JOBMANAGER_CONTAINER",
        "agentic-operational-intelligence-platform-flink-jobmanager-1",
    )
    jobs_dir = os.environ.get("FLINK_JOBS_DIR", "/opt/flink/usrlib/flink_job")
    pyfs_root = os.environ.get("PYFS_ROOT", "/opt/flink/usrlib")

    logger.info(
        "Submitting %d pipeline(s) to jobmanager '%s'%s",
        len(PIPELINES),
        jobmanager,
        "  [DRY RUN]" if args.dry_run else "",
    )

    failed: list[str] = []
    for pipeline in PIPELINES:
        ok = _submit(pipeline, jobmanager=jobmanager, jobs_dir=jobs_dir, pyfs_root=pyfs_root, dry_run=args.dry_run)
        if not ok:
            failed.append(pipeline)

    if failed:
        logger.error("Failed pipelines: %s", ", ".join(failed))
        sys.exit(1)

    logger.info("All %d pipeline(s) submitted. Monitor at http://localhost:8082", len(PIPELINES))


if __name__ == "__main__":
    main()
