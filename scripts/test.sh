#!/usr/bin/env bash
# Run unit tests for weconnect_mvp
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Activating virtualenv"
${ROOT_DIR}/scripts/activate_venv.sh

# Check for -v or --verbose in arguments
if [[ "$@" =~ (\-v|\--verbose) ]]; then
	PYTEST_VERBOSE="--verbose"
	PYTEST_LOG="-o log_cli_level=INFO --log-cli-level=INFO"
else
	PYTEST_VERBOSE=""
	PYTEST_LOG=""
fi

echo "Running tests"
# forward all args to pytest
pytest "${ROOT_DIR}/tests/test_carconnectivity_adapter.py" "${ROOT_DIR}/tests/test_mcp_server.py" "${ROOT_DIR}/tests/test_full_roundtrip.py" $PYTEST_VERBOSE $PYTEST_LOG "$@"
echo "Tests completed successfully"
