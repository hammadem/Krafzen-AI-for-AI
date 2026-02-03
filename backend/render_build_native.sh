#!/bin/bash
set -e

echo "Build script started..."

# 0. Install system dependencies needed for potrace compilation (if on Linux/Ubuntu)
if command -v apt-get &> /dev/null; then
    echo "Installing build dependencies..."
    apt-get update && apt-get install -y \
        wget \
        build-essential \
        automake \
        autoconf \
        || echo "Warning: Some build dependencies may not be installed"
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

# Summary
echo "Build complete."
