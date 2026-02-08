#!/usr/bin/env bash
# Create or recreate the .venv virtual environment and install from requirements.txt
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="$(command -v python3 || command -v python)"
REQ_FILE="$ROOT_DIR/requirements.txt"

echo "Repository root: $ROOT_DIR"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "Python not found on PATH. Please install Python 3.8+ and retry." >&2
  exit 1
fi

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

VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

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
echo "  source $VENV_DIR/bin/activate"
echo "Or run scripts via the venv python directly, e.g.:"
echo "  $VENV_PYTHON -m pytest"
echo "  $VENV_PYTHON -m weconnect_mcp.cli.mcp_server_cli src/config.json"

exit 0
