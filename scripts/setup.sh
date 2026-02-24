#!/usr/bin/env bash
# Create or recreate the .venv virtual environment and install from requirements.txt
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
REQ_FILE="$ROOT_DIR/requirements.txt"

# Source the shared detection library
# shellcheck source=./lib/detect_python.sh
source "$(dirname "$0")/lib/detect_python.sh"

# Detect Python and OS
detect_python || exit 1

# Set venv paths (do this regardless of whether venv exists)
# We define them manually here because get_venv_paths checks if venv exists
if [ "$IS_WINDOWS" = true ]; then
    VENV_PYTHON="$VENV_DIR/Scripts/python.exe"
    VENV_PIP="$VENV_DIR/Scripts/pip.exe"
    VENV_ACTIVATE="$VENV_DIR/Scripts/activate"
else
    VENV_PYTHON="$VENV_DIR/bin/python"
    VENV_PIP="$VENV_DIR/bin/pip"
    VENV_ACTIVATE="$VENV_DIR/bin/activate"
fi

echo "Repository root: $ROOT_DIR"
echo "OS: $OS_TYPE"
echo "System Python: $PYTHON_BIN"

if [ ! -f "$REQ_FILE" ]; then
  echo "requirements.txt not found at $REQ_FILE" >&2
  exit 1
fi

echo "Using Python: $PYTHON_BIN"

if [ -d "$VENV_DIR" ]; then
  read -p ".venv exists. Remove and recreate? [y/N]: " yn
  yn=${yn:-N}
  if [[ "$yn" =~ ^[Yy]$ ]]; then
    rm -rf "$VENV_DIR"
  else
    echo "Leaving existing .venv in place. To force recreation, remove $VENV_DIR and rerun." 
    exit 0
  fi
fi

echo "Creating virtualenv at $VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"

echo "Upgrading pip inside venv..."
"$VENV_PYTHON" -m pip install --upgrade pip setuptools wheel

echo "Installing requirements from $REQ_FILE"
"$VENV_PIP" install -r "$REQ_FILE"

# Setup configuration file
CONFIG_EXAMPLE="$ROOT_DIR/src/config.example.json"
CONFIG_FILE="$ROOT_DIR/src/config.json"

if [ ! -f "$CONFIG_FILE" ]; then
  if [ -f "$CONFIG_EXAMPLE" ]; then
    echo ""
    echo "Creating config.json from example..."
    cp "$CONFIG_EXAMPLE" "$CONFIG_FILE"
    echo "⚠️  IMPORTANT: Edit src/config.json with your VW WeConnect credentials!"
    echo "   - username: Your VW account email"
    echo "   - password: Your VW account password"
    echo "   - spin: Your VW S-PIN (4 digits)"
  else
    echo "Warning: config.example.json not found, skipping config file creation" >&2
  fi
else
  echo "Config file already exists at $CONFIG_FILE (not overwriting)"
fi

echo ""
echo "Done. To activate the venv, run:"
if [ "$IS_WINDOWS" = true ]; then
  echo "  $VENV_DIR\\Scripts\\activate  (CMD)"
  echo "  . $VENV_DIR/Scripts/activate  (Bash)"
else
  echo "  source $VENV_DIR/bin/activate"
fi
echo ""
echo "Or run scripts via the venv python directly, e.g.:"
echo "  $VENV_PYTHON -m pytest"
echo "  $VENV_PYTHON -m weconnect_mcp.cli.mcp_server_cli src/config.json"

exit 0
