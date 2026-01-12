#!/bin/bash
set -e

echo "Build script started..."

# 1. Install Python Dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# 2. Install Potrace locally (since we don't have sudo/apt in Native env)
POTRACE_VERSION="1.16"
INSTALL_DIR="$HOME/.local"
POTRACE_BIN="$INSTALL_DIR/bin/potrace"

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
