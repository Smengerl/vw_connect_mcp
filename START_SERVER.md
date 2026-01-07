Start scripts for the MCP-like HTTP server

This project provides a few convenience shell scripts to start the local MCP-like HTTP server implemented in `src/mcp_server_cli.py`.

Scripts

- `start_server.sh` (existing): basic starter (runs `python3 mcp_server_cli.py src/config.json -v`).
- `start_server_fg.sh`: start server in foreground, useful for debugging.
  Usage: `./start_server_fg.sh [config.json] [port]`
  Defaults: `src/config.json`, port `8765`.

- `start_server_bg.sh`: start server in background using `nohup` and write logs to `logs/server.log` and pid to `logs/server.pid`.
  Usage: `./start_server_bg.sh [config.json] [port]`

- `start_server_port.sh`: wrapper to start on a specific port.
  Usage: `./start_server_port.sh PORT [config.json]`

- `stop_server_bg.sh`: stop a background server started by `start_server_bg.sh` (reads `logs/server.pid` by default).
  Usage: `./stop_server_bg.sh [pidfile]`

Notes

- All scripts call `python3 src/mcp_server_cli.py <config> --serve --port <port>` so ensure you have valid credentials and connectivity when starting.
- Adjust `--tokenstorefile` path inside the scripts if you want a persistent tokenstore location.
- The background starter creates a `logs/` directory (if missing) and writes `server.log` and `server.pid` there.

Example

Start in background on default port:

./start_server_bg.sh

Tail logs:

tail -F logs/server.log
