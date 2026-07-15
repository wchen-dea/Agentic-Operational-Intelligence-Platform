#!/usr/bin/env python3
"""Register all Avro schemas from /schemas into the Confluent Schema Registry.

Subject name convention:  <namespace>.<name>-value  (Avro full name + "-value")
                          e.g. CanonicalKronosCrewtime-value
Schema type:              AVRO
Idempotent:               already-registered schemas are skipped (HTTP 409 / error code 40901).

Usage (docker-compose mounts this file at /register_schemas.py):
    python3 /register_schemas.py

Environment variables:
    SCHEMA_REGISTRY_URL  Base URL of the Schema Registry (default: http://schema-registry:8081)
    SCHEMAS_DIR          Directory containing .avsc files     (default: /schemas)
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

SCHEMA_REGISTRY_URL = os.environ.get("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")
SCHEMAS_DIR = os.environ.get("SCHEMAS_DIR", "/schemas")
MAX_WAIT_SECONDS = 60


def wait_for_registry(base: str, max_wait: int = MAX_WAIT_SECONDS) -> None:
    """Block until the Schema Registry /subjects endpoint responds."""
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f"{base}/subjects", timeout=3)
            return
        except Exception:
            print(f"Waiting for Schema Registry at {base} ...")
            time.sleep(3)
    raise RuntimeError(f"Schema Registry at {base} did not become ready within {max_wait}s")


def register_schema(base: str, subject: str, schema_text: str) -> tuple[str, int | None]:
    """
    POST a schema to /subjects/{subject}/versions.

    Returns:
        ("ok", id)       on success
        ("skipped", None) if already registered (HTTP 409 / error code 40901)
        ("failed", None)  on any other error
    """
    payload = json.dumps({"schema": schema_text, "schemaType": "AVRO"}).encode()
    url = f"{base}/subjects/{subject}/versions"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            schema_id: int = json.loads(resp.read())["id"]
            return "ok", schema_id
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        # 40901 = schema already registered; treat as success
        if exc.code == 409 or "40901" in body:
            return "skipped", None
        print(f"  HTTP {exc.code}: {body[:200]}", file=sys.stderr)
        return "failed", None
    except Exception as exc:
        print(f"  Error: {exc}", file=sys.stderr)
        return "failed", None


def main() -> int:
    print(f"Schema Registry : {SCHEMA_REGISTRY_URL}")
    print(f"Schemas dir     : {SCHEMAS_DIR}")
    print()

    wait_for_registry(SCHEMA_REGISTRY_URL)

    files = sorted(f for f in os.listdir(SCHEMAS_DIR) if f.endswith(".avsc"))
    if not files:
        print("No .avsc files found - nothing to register.")
        return 0

    counts = {"ok": 0, "skipped": 0, "failed": 0}

    for fname in files:
        path = os.path.join(SCHEMAS_DIR, fname)
        schema_text = open(path, encoding="utf-8").read()

        # Derive subject from the schema's namespace + name (Avro full name)
        # so the subject aligns with the topic name used by producers/consumers.
        # Subject convention: <namespace>.<name>-value
        try:
            schema_obj = json.loads(schema_text)
            ns = schema_obj.get("namespace", "")
            name = schema_obj.get("name", "")
            full = f"{ns}.{name}" if ns else name
            subject = f"{full}-value"
        except (json.JSONDecodeError, AttributeError):
            # Fallback: use filename stem (e.g. kronos.hours-value)
            subject = fname[:-5] + "-value"

        status, schema_id = register_schema(SCHEMA_REGISTRY_URL, subject, schema_text)
        counts[status] += 1

        if status == "ok":
            print(f"  OK      {subject:<55}  id={schema_id}")
        elif status == "skipped":
            print(f"  SKIP    {subject:<55}  (already registered)")
        else:
            print(f"  FAIL    {subject}", file=sys.stderr)

    print()
    print(f"Done: {counts['ok']} registered, {counts['skipped']} skipped, {counts['failed']} failed.")
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
