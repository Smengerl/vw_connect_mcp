#!/usr/bin/env bash
# Create or recreate the .venv virtual environment and install the local package in editable mode
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

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

echo "Installing project in editable mode"
"$VENV_PIP" install -e "$ROOT_DIR"

# Setup Tibber credentials file
CONFIG_EXAMPLE="$ROOT_DIR/src/tibber_config.example.json"
CONFIG_FILE="$ROOT_DIR/src/tibber_config.json"

if [ ! -f "$CONFIG_FILE" ]; then
  if [ -f "$CONFIG_EXAMPLE" ]; then
    echo ""
    echo "Creating tibber_config.json from example..."
    cp "$CONFIG_EXAMPLE" "$CONFIG_FILE"
    echo "⚠️  IMPORTANT: Edit src/tibber_config.json with your Tibber OAuth2 client!"
    echo "   Register a client at https://data-api.tibber.com/clients/manage/"
    echo "   - client_id / client_secret: from that registration"
    echo "   - redirect_uri: must match what you registered (default: http://localhost:8515/callback)"
    echo "   Then run the one-time interactive login:"
    echo "     $VENV_PYTHON -m weconnect_mcp.cli.tibber_login_cli"
  else
    echo "Warning: tibber_config.example.json not found, skipping config file creation" >&2
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
echo "  $VENV_PYTHON -m weconnect_mcp.cli.mcp_server_cli src/tibber_config.json"

exit 0
