#!/bin/bash
set -e

echo "Build script started..."

# 0. Install system dependencies for potrace (optional; skip on read-only FS e.g. Render)
if command -v apt-get &> /dev/null; then
    echo "Installing build dependencies (optional)..."
    (apt-get update && apt-get install -y wget build-essential automake autoconf) || echo "Warning: Skipping apt (e.g. read-only filesystem); continuing without system deps."
fi

# 1. Install Python Dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# 2. Install Potrace locally (force into project dir to ensure persistence)
POTRACE_VERSION="1.16"
# Use absolute path to project src
INSTALL_DIR="$(pwd)/bin"
POTRACE_BIN="$INSTALL_DIR/bin/potrace"

echo "Installing Potrace to: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

if [ ! -f "$POTRACE_BIN" ]; then
    echo "Potrace not found. Compiling from source..."
    
    # Create temp dir
    mkdir -p tmp_potrace
    cd tmp_potrace
    
    # Download
    wget "https://sourceforge.net/projects/potrace/files/$POTRACE_VERSION/potrace-$POTRACE_VERSION.tar.gz" -O potrace.tar.gz
    tar -xzf potrace.tar.gz
    cd "potrace-$POTRACE_VERSION"
    
    # Configure and Install to local user directory
    ./configure --prefix="$INSTALL_DIR"
    make
    make install
    
    # Cleanup
    cd ../..
    rm -rf tmp_potrace
    
    echo "Potrace installed successfully to $POTRACE_BIN"
else
    echo "Potrace already installed at $POTRACE_BIN"
fi

# 3. Optional ODA File Converter for DWG export (Render Linux builds)
# Set DWG_ODA_DEB_URL in the Render service to a direct HTTPS URL of the official Linux x64 .deb
# (obtain from https://www.opendesign.com/guestfiles/oda_file_converter — do not commit the .deb).
INSTALL_ODA_SH="$(pwd)/docker/install_oda_file_converter.sh"
if [ -n "${DWG_ODA_DEB_URL:-}" ] && [ -f "$INSTALL_ODA_SH" ] && command -v apt-get &> /dev/null; then
    echo "Installing ODA File Converter from DWG_ODA_DEB_URL..."
    bash "$INSTALL_ODA_SH" from-url "$DWG_ODA_DEB_URL"
elif [ -n "${DWG_ODA_DEB_URL:-}" ]; then
    echo "Warning: DWG_ODA_DEB_URL is set but $INSTALL_ODA_SH not found or apt-get unavailable; skipping ODA install."
fi

# Summary
echo "Build complete."
