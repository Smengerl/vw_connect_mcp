#!/usr/bin/env bash
# Stop background server started with start_server_bg.sh by reading pidfile.
# Usage: ./stop_server_bg.sh [pidfile]
PID_FILE=${1:-logs/server.pid}

if [ ! -f "${PID_FILE}" ]; then
  echo "pidfile ${PID_FILE} not found"
  exit 1
fi
PID=$(cat "${PID_FILE}")
if kill -0 "${PID}" >/dev/null 2>&1; then
  echo "Stopping server pid ${PID}"
  kill "${PID}"
  sleep 1
  if kill -0 "${PID}" >/dev/null 2>&1; then
    echo "PID ${PID} did not exit, sending SIGKILL"
    kill -9 "${PID}" || true
  fi
  rm -f "${PID_FILE}"
  echo "Stopped"
else
  echo "No process ${PID} running — removing stale pidfile"
  rm -f "${PID_FILE}"
fi
