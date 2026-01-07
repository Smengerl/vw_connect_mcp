#!/usr/bin/env bash
# Start the weconnect_mvp server on a specific port.
# Usage: ./start_server_port.sh PORT [config.json]
# Example: ./start_server_port.sh 8080 src/config.json
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

set -euo pipefail
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 PORT [config.json]"
  exit 1
fi
PORT=$1
CONFIG=${2:-src/config.json}

exec "start_server_fg.sh" "${CONFIG}" "${PORT}"
