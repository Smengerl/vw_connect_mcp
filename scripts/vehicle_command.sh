#!/usr/bin/env bash
# Send commands to VW vehicles using CarConnectivityAdapter
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Print usage if no arguments or help requested
if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "Send commands to VW vehicles using CarConnectivityAdapter"
    echo ""
    echo "Usage: $0 <vehicle_id> <command>"
    echo ""
    echo "Available Commands:"
    echo "  Lock/Unlock:"
    echo "    lock, unlock"
    echo ""
    echo "  Climatization:"
    echo "    start_climatization, stop_climatization"
    echo ""
    echo "  Charging (BEV/PHEV only):"
    echo "    start_charging, stop_charging"
    echo ""
    echo "  Lights/Horn:"
    echo "    flash_lights, honk_and_flash"
    echo ""
    echo "  Window Heating:"
    echo "    start_window_heating, stop_window_heating"
    echo ""
    echo "Examples:"
    echo "  $0 ID7 lock"
    echo "  $0 Golf unlock"
    echo "  $0 ID7 start_climatization"
    echo "  $0 ID7 start_charging"
    echo ""
    exit 0
fi

# Activate virtualenv
echo "Activating virtualenv..."
${ROOT_DIR}/scripts/activate_venv.sh

# Run the Python script with all arguments
python "${ROOT_DIR}/scripts/vehicle_command.py" "$@"
