
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

2. **Create and activate a virtual environment**  
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies in editable mode**  
   ```bash
   pip install -e .
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

#### 1. Foreground (with logs to console)
```bash
./start_server_fg.sh [config.json] [port]
```

#### 2. Background (with logs to file)
```bash
./start_server_bg.sh [config.json] [port]
```

#### 3. Directly via Python
```bash
python -m weconnect_mcp.cli.mcp_server_cli path/to/config.json --port 8765
```

#### 4. After editable install (console script)
```bash
weconnect-mvp-server path/to/config.json --port 8765
```

### Stopping the Server

If started in the background, stop the server using the stored PID or your process manager.

---

## Testing

Run the test suite with:
```bash
./run_tests.sh
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

