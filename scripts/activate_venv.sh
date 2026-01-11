#!/usr/bin/env bash
# Activate repository's virtualenv Python
# This script can be sourced to activate the venv in the current shell.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Virtualenv python not found at $VENV_PYTHON"
  echo "Activate your venv or adjust the path in this script."
  exit 1
fi
