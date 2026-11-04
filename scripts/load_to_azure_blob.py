#!/usr/bin/env python3
"""
Upload the raw CSV extracts to Azure Blob Storage / ADLS Gen2 (the landing zone).

Not executed in CI -- it needs a real storage account. Configuration via environment variables:

  AZURE_STORAGE_CONNECTION_STRING   (required) storage account connection string
  AZURE_STORAGE_CONTAINER           (optional) container / ADLS filesystem, default "raw"
  AZURE_STORAGE_PREFIX              (optional) folder prefix, default "kenya_retail"

Files land at  <container>/<prefix>/<table>/load_date=YYYY-MM-DD/<table>.csv  -- a Hive-style
partition layout that Synapse COPY INTO / OPENROWSET and ADF can read directly.

Usage:
  export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=...;..."
  python scripts/load_to_azure_blob.py                 # upload data/raw/*.csv
  python scripts/load_to_azure_blob.py --dry-run       # show what would be uploaded
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ["customers", "products", "orders", "order_items", "payments", "marketing_spend"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Upload raw CSVs to Azure Blob / ADLS Gen2")
    ap.add_argument("--source", type=Path, default=ROOT / "data" / "raw")
    ap.add_argument("--container", default=os.environ.get("AZURE_STORAGE_CONTAINER", "raw"))
    ap.add_argument("--prefix", default=os.environ.get("AZURE_STORAGE_PREFIX", "kenya_retail"))
    ap.add_argument("--load-date", default=dt.date.today().isoformat())
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = [(t, args.source / f"{t}.csv") for t in TABLES]
    missing = [str(p) for _, p in files if not p.exists()]
    if missing:
        print(f"Missing raw files (run `make data`): {missing}", file=sys.stderr)
        return 1

    plan = [(p, f"{args.prefix}/{t}/load_date={args.load_date}/{t}.csv") for t, p in files]
    if args.dry_run:
        for p, blob in plan:
            print(f"[dry-run] {p} -> {args.container}/{blob}")
        return 0

    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str:
        print("AZURE_STORAGE_CONNECTION_STRING is not set.", file=sys.stderr)
        return 1

    # Imported lazily so the rest of the project runs without the Azure SDK installed.
    from azure.core.exceptions import ResourceExistsError
    from azure.storage.blob import BlobServiceClient, ContentSettings

    service = BlobServiceClient.from_connection_string(conn_str)
    container = service.get_container_client(args.container)
    try:
        container.create_container()
        print(f"Created container '{args.container}'")
    except ResourceExistsError:
        pass

    for path, blob_name in plan:
        with path.open("rb") as fh:
            container.upload_blob(
                name=blob_name,
                data=fh,
                overwrite=True,  # re-running a load date is idempotent
                content_settings=ContentSettings(content_type="text/csv"),
                max_concurrency=4,
            )
        print(f"Uploaded {path.name:<20} {path.stat().st_size / 1e6:6.1f} MB -> {args.container}/{blob_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
