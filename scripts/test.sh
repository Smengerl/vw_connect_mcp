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
SKIP_SLOW=false
PYTEST_ARGS=()

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
        *)
            PYTEST_ARGS+=("$arg")
            ;;
    esac
done

echo "Activating virtualenv"
# Source activation script
if [ -f "$VENV_ACTIVATE" ]; then
  # shellcheck disable=SC1090
  source "$VENV_ACTIVATE"
fi

# Build pytest command
PYTEST_CMD=("$VENV_PYTHON" -m pytest "${ROOT_DIR}/tests/" --capture=no)

# Add markers if skipping slow tests
if [ "$SKIP_SLOW" = true ]; then
    PYTEST_CMD+=(-m "not real_api and not slow")
    echo "Running fast tests only (skipping slow/real_api tests)"
else
    echo "Running ALL tests (including slow real API tests)"
fi

# Add verbose and logging flags
if [ -n "$PYTEST_VERBOSE" ]; then
    PYTEST_CMD+=($PYTEST_VERBOSE)
fi
if [ -n "$PYTEST_LOG" ]; then
    PYTEST_CMD+=($PYTEST_LOG)
fi

# Add any remaining arguments
PYTEST_CMD+=("${PYTEST_ARGS[@]}")

echo "Running tests from: ${ROOT_DIR}/tests/"

# Run pytest on entire tests directory
"${PYTEST_CMD[@]}"

echo "Tests completed successfully"
