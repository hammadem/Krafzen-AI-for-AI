#!/bin/bash
set -euo pipefail

# Resolve backend/ directory from this script so builds work when Render invokes
# `bash backend/render_build_native.sh` with cwd at repo root (not backend/).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Build script started (backend dir: $SCRIPT_DIR)..."

# 0. Install system dependencies for potrace (optional; skip on read-only FS e.g. Render)
if command -v apt-get &> /dev/null; then
    echo "Installing build dependencies (optional)..."
    (apt-get update && apt-get install -y wget build-essential automake autoconf) || echo "Warning: Skipping apt (e.g. read-only filesystem); continuing without system deps."
fi

# 1. Install Python Dependencies
echo "Installing Python dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt"

# 2. Install Potrace locally (force into project dir to ensure persistence)
POTRACE_VERSION="1.16"
INSTALL_DIR="$SCRIPT_DIR/bin"
POTRACE_BIN="$INSTALL_DIR/bin/potrace"

echo "Installing Potrace to: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

if [ ! -f "$POTRACE_BIN" ]; then
    echo "Potrace not found. Compiling from source..."

    TMP_POT="$SCRIPT_DIR/tmp_potrace"
    mkdir -p "$TMP_POT"
    cd "$TMP_POT"

    wget "https://sourceforge.net/projects/potrace/files/$POTRACE_VERSION/potrace-$POTRACE_VERSION.tar.gz" -O potrace.tar.gz
    tar -xzf potrace.tar.gz
    cd "potrace-$POTRACE_VERSION"

    ./configure --prefix="$INSTALL_DIR"
    make
    make install

    cd "$SCRIPT_DIR"
    rm -rf "$TMP_POT"

    echo "Potrace installed successfully to $POTRACE_BIN"
else
    echo "Potrace already installed at $POTRACE_BIN"
fi

# 3. Optional ODA File Converter for DWG export (Render Linux builds)
#
# Render runs build and runtime on different hosts: `dpkg -i` on the build VM installs into /usr
# and is NOT shipped with the deploy artifact — only the repo directory is. Potrace works because
# it installs under backend/bin/. We extract the .deb into backend/.oda_bundle/ so it deploys.
#
# Set DWG_ODA_DEB_URL to a direct HTTPS URL of the official Linux x64 .deb
# (https://www.opendesign.com/guestfiles/oda_file_converter — do not commit the .deb).
if [ -n "${DWG_ODA_DEB_URL:-}" ]; then
    if ! command -v wget >/dev/null 2>&1; then
        echo "ERROR: wget is required to download DWG_ODA_DEB_URL" >&2
        exit 1
    fi
    if ! command -v dpkg-deb >/dev/null 2>&1; then
        echo "ERROR: dpkg-deb not found (install dpkg). Cannot bundle ODA for deploy." >&2
        exit 1
    fi
    DEB_LOCAL="$SCRIPT_DIR/.oda_download.deb"
    ODA_BUNDLE="$SCRIPT_DIR/.oda_bundle"
    echo "Bundling ODA File Converter from DWG_ODA_DEB_URL into $ODA_BUNDLE ..."
    wget -qO "$DEB_LOCAL" "${DWG_ODA_DEB_URL}"
    rm -rf "$ODA_BUNDLE"
    mkdir -p "$ODA_BUNDLE"
    dpkg-deb -x "$DEB_LOCAL" "$ODA_BUNDLE"
    rm -f "$DEB_LOCAL"

    ODA_BIN=""
    if [ -f "$ODA_BUNDLE/usr/bin/ODAFileConverter" ]; then
        ODA_BIN="$ODA_BUNDLE/usr/bin/ODAFileConverter"
    else
        ODA_BIN="$(find "$ODA_BUNDLE" -type f \( -name 'ODAFileConverter' -o -name 'ODAFileConverter_*' \) 2>/dev/null | head -1 || true)"
    fi
    if [ -z "$ODA_BIN" ] || [ ! -f "$ODA_BIN" ]; then
        echo "ERROR: ODAFileConverter binary not found inside extracted .deb under $ODA_BUNDLE" >&2
        exit 1
    fi
    chmod +x "$ODA_BIN" || true

    REL="${ODA_BIN#"$SCRIPT_DIR"/}"
    printf '%s\n' "$REL" > "$ODA_BUNDLE/converter_relpath.txt"

    LD_EXTRA=""
    while IFS= read -r dir; do
        [ -n "$dir" ] || continue
        if [ -z "$LD_EXTRA" ]; then
            LD_EXTRA="$dir"
        else
            LD_EXTRA="$LD_EXTRA:$dir"
        fi
    done < <(find "$ODA_BUNDLE" -name '*.so*' \( -type f -o -type l \) 2>/dev/null | while IFS= read -r f; do dirname "$f"; done | sort -u)

    printf '%s\n' "${LD_EXTRA:-}" > "$ODA_BUNDLE/ld_library_path.txt"
    echo "DWG: bundled ODA converter OK (relative: $REL)"
fi

# Summary
echo "Build complete."
