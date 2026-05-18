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
    for d in "$ODA_BUNDLE/usr/bin"/ODAFileConverter_*; do
        if [ -f "$d/ODAFileConverter" ]; then
            ODA_BIN="$d/ODAFileConverter"
            break
        fi
    done
    if [ -z "$ODA_BIN" ] || [ ! -f "$ODA_BIN" ]; then
        ODA_BIN="$(find "$ODA_BUNDLE" -type f -name 'ODAFileConverter' -path '*/ODAFileConverter_*/*' 2>/dev/null | head -1 || true)"
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

    PLATFORMS_DIR="$(find "$ODA_BUNDLE" -type d -name platforms 2>/dev/null | head -1 || true)"
    if [ -n "$PLATFORMS_DIR" ]; then
        printf '%s\n' "$PLATFORMS_DIR" > "$ODA_BUNDLE/qt_plugin_path.txt"
        if command -v apt-get >/dev/null; then
            apt-get install -y -qq libqt6gui6 libqt6gui6t64 qt6-qpa-plugins 2>/dev/null \
                || apt-get install -y -qq libqt5gui5 qt5-qpa-plugins 2>/dev/null || true
            for QT_SYS in \
                /usr/lib/x86_64-linux-gnu/qt6/plugins/platforms \
                /usr/lib/x86_64-linux-gnu/qt5/plugins/platforms; do
                [ -d "$QT_SYS" ] || continue
                for plugin in libqoffscreen.so libqminimal.so; do
                    if [ -f "$QT_SYS/$plugin" ] && [ ! -f "$PLATFORMS_DIR/$plugin" ]; then
                        cp "$QT_SYS/$plugin" "$PLATFORMS_DIR/"
                        echo "DWG: copied $plugin into $PLATFORMS_DIR"
                    fi
                done
            done
            if [ ! -f "$PLATFORMS_DIR/libqoffscreen.so" ] && [ ! -f "$PLATFORMS_DIR/libqminimal.so" ]; then
                echo "WARNING: no headless Qt plugins; runtime will download qt6-qpa-plugins .deb"
            fi
        fi
        if [ -f "$PLATFORMS_DIR/libqxcb.so" ]; then
            apt-get install -y -qq libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
                libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxkbcommon-x11-0 libxcb-util1 2>/dev/null || true
            XCB_LIBS="$ODA_BUNDLE/xcb_libs"
            mkdir -p "$XCB_LIBS"
            ldd "$PLATFORMS_DIR/libqxcb.so" 2>/dev/null | awk '/=> \// {print $3}' | sort -u | while read -r lib; do
                [ -f "$lib" ] && cp -n "$lib" "$XCB_LIBS/" 2>/dev/null || cp "$lib" "$XCB_LIBS/"
            done
            if [ -f "$XCB_LIBS/libxcb-util.so.1" ] && [ ! -e "$XCB_LIBS/libxcb-util.so.0" ]; then
                ln -sf libxcb-util.so.1 "$XCB_LIBS/libxcb-util.so.0"
            fi
            echo "DWG: vendored xcb libs into $XCB_LIBS"
            if [ -n "${LD_EXTRA:-}" ]; then
                LD_EXTRA="$XCB_LIBS:$LD_EXTRA"
            else
                LD_EXTRA="$XCB_LIBS"
            fi
            printf '%s\n' "$LD_EXTRA" > "$ODA_BUNDLE/ld_library_path.txt"
        fi
    fi

    # Bundle Xvfb binary for xcb-only Qt (run Xvfb directly; no xauth/xvfb-run)
    if [ -n "$PLATFORMS_DIR" ] && [ -f "$PLATFORMS_DIR/libqxcb.so" ] && [ ! -f "$PLATFORMS_DIR/libqoffscreen.so" ] && command -v apt-get >/dev/null; then
        apt-get install -y -qq xvfb xserver-common || true
        XVFB_OUT="$ODA_BUNDLE/xvfb"
        rm -rf "$XVFB_OUT"
        mkdir -p "$XVFB_OUT"
        if command -v dpkg-deb >/dev/null; then
            apt-get download xvfb xserver-common 2>/dev/null || true
            for deb in ./*.deb; do
                [ -f "$deb" ] && dpkg-deb -x "$deb" "$XVFB_OUT" 2>/dev/null || true
            done
            rm -f ./*.deb 2>/dev/null || true
            if [ -f "$XVFB_OUT/usr/bin/Xvfb" ]; then
                echo "DWG: bundled Xvfb at $XVFB_OUT/usr/bin/Xvfb (for xcb Qt plugin)"
            else
                echo "WARNING: Xvfb binary missing after extract"
            fi
        fi
    fi

    echo "DWG: bundled ODA converter OK (relative: $REL)"
fi

# Summary
echo "Build complete."
