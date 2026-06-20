#!/usr/bin/env python3
"""List/inspect Orcasound's public labeled killer-whale data (no credentials).

Orcasound hosts open, anonymously-readable AWS S3 buckets containing
killer-whale call annotations, including the Ford-Osborne SRKW stereotyped
call catalogue and the Pod.Cast labeled archive. This tool enumerates the
relevant prefixes so we can assess whether call-type labels (the piece the
DCLDE corpus lacks) are usable for a repertoire / context analysis.

Read-only by default (list). Use --download <key> --dest <path> to pull one
object. Nothing is written to Git-tracked locations automatically.

Usage:
  python scripts/fetch_orcasound_labels.py --list labeled-data/
  python scripts/fetch_orcasound_labels.py --bucket acoustic-sandbox --list labeled-data/classification/killer-whales/
"""

from __future__ import annotations

import argparse
import sys

import boto3
from botocore import UNSIGNED
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

DEFAULT_BUCKET = "acoustic-sandbox"


def client():
    return boto3.client("s3", config=Config(signature_version=UNSIGNED))


def list_prefix(bucket: str, prefix: str, max_keys: int) -> int:
    s3 = client()
    paginator = s3.get_paginator("list_objects_v2")
    n = 0
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/"):
            for cp in page.get("CommonPrefixes", []):
                print(f"[dir]  {cp['Prefix']}")
            for obj in page.get("Contents", []):
                size_kb = obj["Size"] / 1024
                print(f"[file] {obj['Key']}  ({size_kb:,.1f} KB)")
                n += 1
                if n >= max_keys:
                    print(f"... (truncated at {max_keys} files)")
                    return n
    except (ClientError, BotoCoreError) as exc:
        print(f"ERROR accessing s3://{bucket}/{prefix}: {exc}")
        return -1
    return n


def download(bucket: str, key: str, dest: str) -> int:
    s3 = client()
    try:
        s3.download_file(bucket, key, dest)
        print(f"Downloaded s3://{bucket}/{key} -> {dest}")
        return 0
    except (ClientError, BotoCoreError) as exc:
        print(f"ERROR downloading s3://{bucket}/{key}: {exc}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--list", dest="prefix", default="")
    parser.add_argument("--max-keys", type=int, default=60)
    parser.add_argument("--download", default=None, help="object key to download")
    parser.add_argument("--dest", default=None, help="local destination path for --download")
    args = parser.parse_args()

    if args.download:
        if not args.dest:
            print("ERROR: --download requires --dest")
            return 1
        return download(args.bucket, args.download, args.dest)

    print(f"Listing s3://{args.bucket}/{args.prefix} (anonymous)\n")
    n = list_prefix(args.bucket, args.prefix, args.max_keys)
    if n >= 0:
        print(f"\n{n} file(s) listed at this level.")
    return 0 if n >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
