#!/usr/bin/env bash
# Fetch ODA .deb (URL, R2, or local file) and install with apt/dpkg + Qt headless deps.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SH="$SCRIPT_DIR/install_oda_file_converter.sh"
DEB_LOCAL="/tmp/oda_file_converter.deb"
LOCAL_DEB="/tmp/docker-build/oda-file-converter.deb"

if [ -f "$LOCAL_DEB" ]; then
    echo "ODA: installing from build-context docker/oda-file-converter.deb"
    "$INSTALL_SH" from-file "$LOCAL_DEB"
    exit 0
fi

if [ -n "${DWG_ODA_DEB_URL:-}" ] || { [ -n "${R2_ACCESS_KEY_ID:-}" ] && [ -n "${R2_SECRET_ACCESS_KEY:-}" ] && [ -n "${R2_ENDPOINT_URL:-}" ]; }; then
    pip install --no-cache-dir boto3
    python3 "$SCRIPT_DIR/download_oda_deb.py" "$DEB_LOCAL"
    "$INSTALL_SH" from-file "$DEB_LOCAL"
    rm -f "$DEB_LOCAL"
    exit 0
fi

echo "ERROR: ODA not installed — set R2_* or DWG_ODA_DEB_URL on the Render service (used at Docker build time)." >&2
exit 1
