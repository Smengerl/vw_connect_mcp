
# weconnect_mvp

**MCP Server for Volkswagen Vehicles**  
A developer-focused server that exposes information from VW vehicles via a Model Context Protocol (MCP) interface. This project is designed for integration, automation, and experimentation with connected car data.

---

## Features

- **MCP Server**: Provides a standard MCP interface for accessing vehicle data.
- **Volkswagen Integration**: Connects to VW vehicles using the `carconnectivity` library.
- **Flexible CLI**: Multiple scripts and options for starting the server in different modes.
- **Configurable**: Easily adapt connection and authentication settings via a config file.

---

## Getting Started

### Prerequisites

- Python 3.8+
- VW account credentials (username, password, and optionally a spin)
- (Recommended) Virtual environment

### Installation

1. **Clone the repository**  
   ```bash
   git clone <repo-url>
   cd weconnect_mvp
   ```

2. **Create and activate a virtual environment and install dependencies**  
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

	You can use the convenience scripts to automatically set up everything:
	```bash
	./scripts/setup.sh
	```

---

## Configuration

The server requires a configuration file (default: `src/config.json`).  
**You must edit this file to provide your VW credentials and adjust settings as needed.**

Example (`src/config.json`):
```json
{
	"carConnectivity": {
		"log_level": "debug",
		"connectors": [
			{
				"type": "volkswagen",
				"disabled": false,
				"config": {
					"log_level": "error",
					"interval": 300,
					"username": "your@email.com",
					"password": "your_password",
					"spin": "your_spin",
					"api_log_level": "debug",
					"max_age": 300,
					"force_enable_access": false
				}
			}
		],
		"plugins": []
	}
}
```
**Do not commit your credentials!**  
Copy and edit `src/config.json` as needed.


---

## Usage

### CLI Options

You can start the MCP server using the provided CLI scripts or directly via Python:

#### 1. Starting the server in foreground (with logs to console)
```bash
./scripts/start_server_fg.sh
```

#### 2. Starting the server in background (with logs to file)
```bash
./scripts/start_server_bg.sh
```

#### 3. Starting the server directly via Python
```bash
python -m weconnect_mcp.cli.mcp_server_cli path/to/config.json --port 8765
```

### 4. Stopping the Server

If started in the background, stop the server using the script:
```bash
./scripts/stop_server.sh
```

Alternatively, kill the process via PID.
---

## CLI Parameters

The MCP server can be started with several command-line parameters to control its behavior:

| Parameter           | Default                                   | Description                                                      |
|---------------------|-------------------------------------------|------------------------------------------------------------------|
| `config`            | (required)                                | Path to the configuration file                                   |
| `--tokenstorefile`  | `/tmp/tokenstore`                         | Path for the token store file                                    |
| `--log-level`       | (none; uses default if not set)           | Set logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `--log-file`        | (stdout only)                             | Path to log file (if not set, logs to stdout only)               |
| `--transport`       | `http`                                    | Transport mode: `http` or `stdio`                                |
| `--port`            | `8667`                                    | Port for HTTP mode                                               |

**Example:**

```bash
python -m weconnect_mcp.cli.mcp_server_cli src/config.json --log-level DEBUG --log-file server.log --transport http --port 8765
```

---

---

## Testing

Run the test suite with:
```bash
./scripts/tests.sh
```
or
```bash
pytest ./tests/test_mcp_server.py --verbose --asyncio-mode=auto
```

---

## Development Notes

- The main package source is under `src/`.
- For development, always use a virtual environment and install in editable mode.
- The CLI scripts activate the virtual environment automatically.

---

## Contributing

Contributions are welcome! Please see `CONTRIBUTING.md` and follow the code of conduct.

---

## License

This project is licensed under the terms of the MIT License. See `LICENSE.txt` for details.

---

