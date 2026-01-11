#!/usr/bin/env bash
# Run unit tests for weconnect_mvp
set -euo pipefail

echo "Running tests"
source .venv/bin/activate

# Check for -v or --verbose in arguments
if [[ "$@" =~ (\-v|\--verbose) ]]; then
	PYTEST_VERBOSE="--verbose"
	PYTEST_LOG="-o log_cli_level=INFO --log-cli-level=INFO"
else
	PYTEST_VERBOSE=""
	PYTEST_LOG=""
fi

pytest tests/test_mcp_server.py --asyncio-mode=auto $PYTEST_VERBOSE $PYTEST_LOG "$@"
echo "Tests completed successfully"