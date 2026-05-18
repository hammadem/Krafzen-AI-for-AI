#!/usr/bin/env python3
"""Download ODA .deb at Docker build time (R2 API or DWG_ODA_DEB_URL)."""
from __future__ import annotations

import os
import sys
import urllib.request


def _download_r2(dest: str) -> None:
    import boto3
    from botocore.config import Config

    access = os.environ.get("R2_ACCESS_KEY_ID", "").strip()
    secret = os.environ.get("R2_SECRET_ACCESS_KEY", "").strip()
    endpoint = os.environ.get("R2_ENDPOINT_URL", "").strip().rstrip("/")
    bucket = os.environ.get("R2_ODA_BUCKET", "krafzen-build-private").strip()
    key = os.environ.get("R2_ODA_OBJECT_KEY", "ODAFileConverter_QT6_lnxX64_8.3dll_27.1.deb").strip()
    if not (access and secret and endpoint):
        raise RuntimeError("R2 credentials incomplete")
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name="auto",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    client.download_file(bucket, key, dest)
    print(f"Downloaded ODA .deb from R2 s3://{bucket}/{key}")


def _download_url(url: str, dest: str) -> None:
    req = urllib.request.Request(url, headers={"Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        if resp.status >= 400:
            raise RuntimeError(f"HTTP {resp.status} downloading {url}")
        with open(dest, "wb") as out:
            out.write(resp.read())
    print(f"Downloaded ODA .deb from URL ({os.path.getsize(dest)} bytes)")


def main() -> int:
    dest = sys.argv[1] if len(sys.argv) > 1 else "/tmp/oda_file_converter.deb"
    url = os.environ.get("DWG_ODA_DEB_URL", "").strip()
    try:
        if url:
            _download_url(url, dest)
            return 0
        _download_r2(dest)
        return 0
    except Exception as exc:
        print(f"ODA deb download failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
