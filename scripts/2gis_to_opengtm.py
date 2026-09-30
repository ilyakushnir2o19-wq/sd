#!/usr/bin/env python3
"""Normalize parser-2gis-new JSON and optionally ingest it into OpenGTM.

Examples:

  # Normalize only
  python scripts/2gis_to_opengtm.py data/2gis/quick.json --city moscow \
      --output data/2gis/quick-opengtm.json

  # Normalize + push into a workbook
  OPENGTM_URL=https://gtm.example.com \
  OPENGTM_2GIS_WORKBOOK_ID=... \
  OPENGTM_2GIS_INGEST_TOKEN=wbi_... \
  python scripts/2gis_to_opengtm.py data/2gis/quick.json --city moscow --ingest
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests

from apps.api.services.leadgen.twogis import normalize_2gis_rows


BATCH_SIZE = 500


def _load(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict):
        for key in ("rows", "items", "results", "data"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    if not isinstance(data, list):
        raise ValueError("2GIS input must be a JSON array (or an object with rows/items/results/data)")
    return [row for row in data if isinstance(row, dict)]


def _chunks(rows: list[dict[str, Any]], size: int = BATCH_SIZE):
    for i in range(0, len(rows), size):
        yield i // size, rows[i:i + size]


def _base_url(value: str) -> str:
    return (value or "").strip().rstrip("/")


def ingest(
    rows: list[dict[str, Any]],
    *,
    opengtm_url: str,
    workbook_id: str,
    token: str,
    source_fingerprint: str,
    timeout: float = 30.0,
) -> dict[str, Any]:
    if not rows:
        return {"added": 0, "skipped_duplicates": 0, "batches": 0}

    base = _base_url(opengtm_url)
    if not base or not workbook_id or not token:
        raise ValueError("OPENGTM_URL, workbook id and ingest token are all required")

    endpoint = f"{base}/api/v2/workbooks/{workbook_id}/rows/ingest"
    totals = {
        "added": 0,
        "skipped_duplicates": 0,
        "skipped_empty": 0,
        "batches": 0,
        "total_rows": None,
        "unmapped_keys": set(),
    }

    for batch_idx, batch in _chunks(rows):
        idem = f"2gis-{source_fingerprint[:32]}-{batch_idx}"
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": idem,
                "Content-Type": "application/json",
                "User-Agent": "OpenGTM-2GIS-Bridge/1.0",
            },
            json={"rows": batch, "dedupe": True},
            timeout=timeout,
        )
        if response.status_code >= 400:
            body = response.text[:500]
            raise RuntimeError(
                f"OpenGTM ingest failed: HTTP {response.status_code}: {body}"
            )
        payload = response.json()
        totals["added"] += int(payload.get("added") or 0)
        totals["skipped_duplicates"] += int(payload.get("skipped_duplicates") or 0)
        totals["skipped_empty"] += int(payload.get("skipped_empty") or 0)
        totals["batches"] += 1
        totals["total_rows"] = payload.get("total_rows")
        totals["unmapped_keys"].update(payload.get("unmapped_keys") or [])

    totals["unmapped_keys"] = sorted(totals["unmapped_keys"])
    return totals


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--city", default="")
    parser.add_argument("--discovery-url", default="")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ingest", action="store_true")
    parser.add_argument("--opengtm-url", default=os.getenv("OPENGTM_URL", ""))
    parser.add_argument(
        "--workbook-id",
        default=os.getenv("OPENGTM_2GIS_WORKBOOK_ID", ""),
    )
    parser.add_argument(
        "--token",
        default=os.getenv("OPENGTM_2GIS_INGEST_TOKEN", ""),
    )
    args = parser.parse_args()

    raw_bytes = args.input.read_bytes()
    raw = _load(args.input)
    normalized = normalize_2gis_rows(
        raw,
        city=args.city,
        discovery_url=args.discovery_url,
    )

    output = args.output or args.input.with_name(args.input.stem + "-opengtm.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "input_rows": len(raw),
                "normalized_rows": len(normalized),
                "output": str(output),
            },
            ensure_ascii=False,
        )
    )

    if not args.ingest:
        return 0

    fingerprint = hashlib.sha256(raw_bytes).hexdigest()
    result = ingest(
        normalized,
        opengtm_url=args.opengtm_url,
        workbook_id=args.workbook_id,
        token=args.token,
        source_fingerprint=fingerprint,
    )
    print(json.dumps({"ingest": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
