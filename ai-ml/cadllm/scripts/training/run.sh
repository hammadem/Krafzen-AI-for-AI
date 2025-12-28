#!/usr/bin/env bash
set -euo pipefail

# Check if tmux is installed, install if not
if ! command -v tmux &> /dev/null; then
    echo "tmux not found. Installing tmux..."
    if command -v apt-get &> /dev/null; then
        apt-get update -qq && apt-get install -y -qq tmux
    elif command -v yum &> /dev/null; then
        yum install -y -q tmux
    else
        echo "Error: Cannot find package manager (apt-get or yum). Please install tmux manually."
        exit 1
    fi
    
    # Verify installation
    if ! command -v tmux &> /dev/null; then
        echo "Error: tmux installation failed. Please install tmux manually."
        exit 1
    fi
    echo "tmux installed successfully."
fi

# Check and install Python dependencies from requirements.txt
REQUIREMENTS_FILE="requirements.txt"
if [[ -f "$REQUIREMENTS_FILE" ]]; then
    echo "Checking Python dependencies from $REQUIREMENTS_FILE..."
    
    # Check if pip is available
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        echo "Error: pip not found. Please install pip first."
        exit 1
    fi
    
    # Use pip3 if available, otherwise pip
    PIP_CMD="pip3"
    if ! command -v pip3 &> /dev/null; then
        PIP_CMD="pip"
    fi
    
    # Install requirements (upgrade existing packages if needed)
    echo "Installing/updating dependencies from $REQUIREMENTS_FILE..."
    $PIP_CMD install --upgrade -q -r "$REQUIREMENTS_FILE"
    
    if [[ $? -eq 0 ]]; then
        echo "✅ Dependencies installed successfully."
    else
        echo "⚠️  Warning: Some dependencies may have failed to install. Continuing anyway..."
    fi
else
    echo "⚠️  Warning: $REQUIREMENTS_FILE not found. Skipping dependency installation."
fi

SESSION="cadllm"

# Training configuration - can be customized here
DATA_PATH="${DATA_PATH:-/workspace/dataset/jsonl/cadllm.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-/workspace/cadllm}"

# Export variables so train.sh can use them
export DATA_PATH
export OUTPUT_DIR

CMD="./train.sh"

# If already inside tmux, run training once in the current pane
if [[ -n "${TMUX-}" ]]; then
  echo "Already inside tmux, running ${CMD} in the current pane..."
  exec ${CMD}
fi

# Not inside tmux: create session if missing, then run train.sh
if ! tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "Creating tmux session '${SESSION}' and starting ${CMD}..."
  exec tmux new-session -s "${SESSION}" "${CMD}"
fi

# Session exists: attach (training should already be running or you can run it manually)
echo "Attaching to existing tmux session '${SESSION}'..."
exec tmux attach -t "${SESSION}"
