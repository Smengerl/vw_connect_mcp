#!/usr/bin/env bash
# Activate repository's virtualenv Python
# This script can be sourced to activate the venv in the current shell.
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

# Source the shared detection library
# shellcheck source=./lib/detect_python.sh
source "$(dirname "$0")/lib/detect_python.sh"

# Detect OS and get venv paths
detect_python || exit 1
get_venv_activate_script "$VENV_DIR"

if [ ! -f "$VENV_ACTIVATE" ]; then
  echo "Virtualenv not found at $VENV_DIR"
  echo "Run ./scripts/setup.sh to create it first."
  exit 1
fi

# Source the activation script
if [ -f "$VENV_ACTIVATE" ]; then
  # shellcheck disable=SC1090
  source "$VENV_ACTIVATE"
else
  echo "Could not find activation script at $VENV_ACTIVATE"
  exit 1
fi
