# Scripts Directory

This directory contains utility scripts for the weconnect_mvp project.

## 🖥️ Platform Support

All scripts now work on:
- **macOS** (Bash / Zsh)
- **Linux** (Bash)
- **Windows** (Git Bash, WSL, MinGW, or PowerShell with Git Bash installed)

Python detection is automatic:
- Uses `python3` on macOS/Linux
- Uses `python` on Windows (falls back to `python3` if available)
- Uses virtualenv paths appropriate for each OS

## 🧰 Shared Library

All scripts now use a centralized Python detection library to eliminate code duplication.

### `lib/detect_python.sh`

Provides platform-aware utilities for:
- Detecting OS type (Windows, macOS, Linux)
- Finding Python executables
- Resolving virtualenv paths (platform-specific)
- Getting configuration file paths for VS Code, Claude Desktop, and Copilot Desktop

**Benefits**:
- ✅ Single source of truth for platform detection
- ✅ Consistent behavior across all scripts
- ✅ Easy to extend for new configuration paths
- ✅ No code duplication

See [lib/README.md](lib/README.md) for detailed documentation and usage examples.

### Running Scripts on Windows

#### Option 1: Git Bash (Recommended)
```bash
# Git Bash handles all scripts transparently
./scripts/setup.sh
./scripts/test.sh --skip-slow
./scripts/create_mcp_config.sh vscode
```

#### Option 2: WSL (Windows Subsystem for Linux)
```bash
# Works exactly like Linux
bash scripts/setup.sh
bash scripts/test.sh
```

#### Option 3: MinGW / MSYS2
```bash
# Same as Git Bash
./scripts/setup.sh
```

#### Option 4: PowerShell with WSL
```powershell
wsl ./scripts/setup.sh
wsl ./scripts/test.sh --skip-slow
```

## Configuring Secrets

The server reads Tibber Data API credentials from a file and/or environment
variables, resolved in this order — **environment variables override a
credentials file** when both are present:

| File (gitignored) | Env vars |
|---|---|
| `src/tibber_config.json` (template: `src/tibber_config.example.json`) | `TIBBER_CLIENT_ID`, `TIBBER_CLIENT_SECRET`, `TIBBER_REDIRECT_URI`, `TIBBER_TOKEN_PATH` |

**Use the file for local/desktop clients** (Claude Desktop, VS Code Copilot,
Microsoft Copilot Desktop) — those launch the server with their own
environment, not your shell's, so anything set via `export` never reaches
it. `create_mcp_config.sh` already generates configs pointing at
the credentials file for exactly this reason; no secrets end up in the
generated `claude_desktop_config.json` / `mcp.json`.

**Use environment variables for Docker/Railway** — see the main README's
[Cloud Deployment](../README.md#cloud-deployment) section.

The server additionally needs a one-time interactive login before first use
(a browser step that can't run inside the MCP server process itself). It
takes the same optional credentials-file argument as the server, with
identical file/env precedence:

```bash
python -m weconnect_mcp.cli.tibber_login_cli src/tibber_config.json   # if using the file
python -m weconnect_mcp.cli.tibber_login_cli                          # if using env vars
```

**For Docker/Railway specifically**, that login can't run inside the
container either, and Tibber has no way to mint a token from
`client_id`/`client_secret` alone (no `client_credentials` grant — confirmed
live, see `ARCHITECTURE.md` §2.3), so a
`refresh_token` must persist across restarts one way or another. The bridge:
run `tibber_login_cli` locally as above, then paste that run's token file
contents into the `TIBBER_TOKEN_JSON` env var (a Railway variable or
`docker-compose.yml`'s `.env`). It seeds `TIBBER_TOKEN_PATH` once, on first
boot only — point that path at a persisted volume (see `docker-compose.yml`'s
`tibber-tokens` volume) so every later token refresh, which rewrites the
file in place, survives future restarts without the now-stale env var ever
being read again.

## Available Scripts

### test.sh
Run the test suite with optional filtering.

```bash
# Run all tests
./scripts/test.sh

# Run only fast mock tests (recommended for CI/CD)
./scripts/test.sh --skip-slow

# Run with verbose output
./scripts/test.sh --skip-slow -v

# Show help
./scripts/test.sh --help
```

**Options:**
- `--skip-slow` - No-op today (kept for forward compatibility); would skip
  'slow'/'real_api'-marked tests if any existed
- `-v, --verbose` - Run pytest in verbose mode
- `-h, --help` - Show help message

**Test Statistics:**
- 47 fast mock/offline tests (~0.1s, no Tibber account needed)
- No slow/real-API tests exist today — the Tibber Data API is read-only, so
  there's nothing beyond what the mock adapter and the extraction-logic
  fixtures already cover

---

### start_server_fg.sh
Start the MCP server in foreground (with console output). No config file
needed if `TIBBER_CLIENT_ID`/`TIBBER_CLIENT_SECRET` are set as env vars; pass
extra `mcp_server_cli` flags after the config argument.

```bash
./scripts/start_server_fg.sh

# With a credentials file and a custom port
./scripts/start_server_fg.sh src/tibber_config.json --port 8765
```

---

### start_server_bg.sh
Start the MCP server in background (with log file output). Same defaults and
flag-forwarding as `start_server_fg.sh` above.

```bash
./scripts/start_server_bg.sh
```

---

### start_server_http.sh
Start the MCP server in HTTP mode with API-key authentication (foreground).
Reads `.env` from the project root if present.

```bash
# Reads TIBBER_CLIENT_ID/SECRET from env or src/tibber_config.json
MCP_API_KEY=secret ./scripts/start_server_http.sh 8089
```

**Required:** `MCP_API_KEY` always, plus either `TIBBER_CLIENT_ID`/
`TIBBER_CLIENT_SECRET` env vars or `src/tibber_config.json` (see
[Configuring Secrets](#configuring-secrets) below).

---

### stop_server_bg.sh
Stop the MCP server running in background.

```bash
./scripts/stop_server_bg.sh
```

---

### setup.sh
Initialize the project (install dependencies, create virtualenv).

```bash
./scripts/setup.sh
```

---

### activate_venv.sh
Activate the Python virtual environment.

```bash
source ./scripts/activate_venv.sh
```

---

### create_mcp_config.sh
Generate an MCP client config for **Claude Desktop**, **Microsoft Copilot
Desktop**, or **VS Code** (GitHub Copilot) — one script, one `--client`-style
positional argument, replacing the three near-identical scripts this project
used to ship. Points the generated config at `src/tibber_config.json` — see
[Configuring Secrets](#configuring-secrets) above for why a file is used here
instead of environment variables. Prints setup instructions if that file
doesn't exist yet.

```bash
./scripts/create_mcp_config.sh claude
./scripts/create_mcp_config.sh copilot-desktop
./scripts/create_mcp_config.sh vscode
```

**Output locations** (staged file → real destination):

| Client | Staged at | Copy to |
|---|---|---|
| `claude` | `tmp/claude_desktop/claude_desktop_config.json` | macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`; Windows: `%APPDATA%\Claude\claude_desktop_config.json`; Linux: varies by distribution |
| `copilot-desktop` | `tmp/copilot_desktop/mcp.json` | macOS: `~/Library/Application Support/Microsoft/Copilot/mcp.json`; Windows: `%APPDATA%\Microsoft\Copilot\mcp.json` |
| `vscode` | `tmp/vscode/mcp.json` | macOS: `~/Library/Application Support/Code/User/mcp.json`; Windows: `%APPDATA%\Microsoft\VSCode\mcp.json`; Linux: `~/.config/Code/User/mcp.json` |

If `jq` is installed and a config already exists at the destination, the
script prints a one-line `jq` merge command instead of you having to hand-edit
JSON. There is no interactive auto-merge wizard any more (VS Code's script
used to have a 4-option menu with automatic backups) — copy the file over (or
run the printed `jq` command) and restart the client yourself.

**After installing the VS Code config specifically:**
- Restart VS Code (`Cmd+Shift+P` → `Developer: Reload Window`)
- Type `/list` in Copilot Chat to verify installation
- Look for tools starting with `mcp_weconnect_` (e.g., `mcp_weconnect_get_vehicles`)
- VS Code automatically prefixes tools with `mcp_{servername}_` to avoid naming conflicts

---

### test_mcp_auth.sh
Run a full MCP OAuth flow against a running server and validate authenticated access via `tools/list`.

```bash
# Default host (=localhost:8089)
./scripts/test_mcp_auth.sh

# Test a custom host
./scripts/test_mcp_auth.sh http://localhost:8089
```

**Requirements:**
- Running MCP server (default: `http://localhost:8089`)
- `.env` file in project root with `MCP_API_KEY=...`
- Existing `.venv` (script activates it automatically)
- `curl` available in your shell

**What it does (end-to-end):**
1. Checks `GET /health`
2. Loads OAuth metadata from `/.well-known/oauth-authorization-server`
3. Registers a test client (`client_credentials`)
4. Requests an access token from `token_endpoint`
5. Calls MCP `tools/list` with `Authorization: Bearer <token>`

**Typical use case:**
- Quick smoke test after local startup or deployment changes
- Verify OAuth + MCP endpoint wiring before configuring external clients (VS Code, Claude, Copilot Desktop)

---

## Development Notes

### Running Tests Before Commit
```bash
# Fast - only mock tests
./scripts/test.sh --skip-slow

# Complete - all tests
./scripts/test.sh
```

### Development Workflow
```bash
# 1. Setup project
./scripts/setup.sh

# 2. Activate venv
source ./scripts/activate_venv.sh

# 3. Make changes to code

# 4. Run tests
./scripts/test.sh --skip-slow

# 5. Commit if all tests pass
```

---

## Exit Codes

All scripts follow standard Unix exit codes:
- `0` - Success
- `1` - Error/Failure

This allows for easy integration in CI/CD pipelines and shell scripts.

## Virtual Environment

All scripts automatically activate the virtual environment using `activate_venv.sh`. You don't need to manually activate it before running scripts.
