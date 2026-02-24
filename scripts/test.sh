#!/usr/bin/env bash
# Run unit tests for weconnect
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Source the shared detection library
# shellcheck source=./lib/detect_python.sh
source "$(dirname "$0")/lib/detect_python.sh"

# Detect Python and get venv paths
detect_python || exit 1
get_venv_paths "$ROOT_DIR/.venv"
get_venv_activate_script "$ROOT_DIR/.venv"

# Print usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Run pytest on all tests in tests/ directory and subdirectories."
    echo ""
    echo "Options:"
    echo "  --skip-slow       Skip tests marked as 'slow' or 'real_api'"
    echo "  -v, --verbose     Run pytest in verbose mode"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests (including slow real API tests)"
    echo "  $0 --skip-slow        # Run only fast mock tests"
    echo "  $0 --skip-slow -v     # Run fast tests with verbose output"
    exit 0
}

# Parse arguments
PYTEST_VERBOSE=""
PYTEST_LOG=""
PYTEST_MARKERS=""
SKIP_SLOW=false

for arg in "$@"; do
    case $arg in
        -h|--help)
            usage
            ;;
        --skip-slow)
            SKIP_SLOW=true
            shift
            ;;
        -v|--verbose)
            PYTEST_VERBOSE="--verbose"
            PYTEST_LOG="-o log_cli_level=INFO --log-cli-level=INFO"
            shift
            ;;
    esac
done

echo "Activating virtualenv"
# Source activation script
if [ -f "$VENV_ACTIVATE" ]; then
  # shellcheck disable=SC1090
  source "$VENV_ACTIVATE"
fi

# Set marker expression to skip slow tests if requested
if [ "$SKIP_SLOW" = true ]; then
    PYTEST_MARKERS="-m \"not real_api and not slow\""
    echo "Running fast tests only (skipping slow/real_api tests)"
else
    echo "Running ALL tests (including slow real API tests)"
fi

echo "Running tests from: ${ROOT_DIR}/tests/"

# Run pytest on entire tests directory
eval "$VENV_PYTHON" -m pytest "${ROOT_DIR}/tests/" $PYTEST_VERBOSE $PYTEST_LOG $PYTEST_MARKERS "$@"

echo "Tests completed successfully"

# Set marker expression to skip slow tests if requested
if [ "$SKIP_SLOW" = true ]; then
    PYTEST_MARKERS="-m \"not real_api and not slow\""
    echo "Running fast tests only (skipping slow/real_api tests)"
else
    echo "Running ALL tests (including slow real API tests)"
fi

echo "Running tests from: ${ROOT_DIR}/tests/"

# Run pytest on entire tests directory
eval pytest "${ROOT_DIR}/tests/" $PYTEST_VERBOSE $PYTEST_LOG $PYTEST_MARKERS "$@"

echo "Tests completed successfully"
