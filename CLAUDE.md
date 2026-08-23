# CLAUDE.md

Project guidance for Claude Code sessions working in this repository.

## What this is

An MCP (Model Context Protocol) server that exposes Volkswagen vehicle data
to AI assistants (Claude Desktop, VS Code Copilot, Claude Code, ChatGPT,
Claude.ai) via the **Tibber Data API** — read-only, since VW blocked direct
third-party API access (see the warning at the top of `README.md`).

There used to be a second backend (`carconnectivity`, VW-direct). It has
been fully removed from `main`; that code lives on permanently, unmaintained,
on the `carconnectivity` git branch. Don't reintroduce dual-backend framing
in code or docs — this project is Tibber-only now.

## Architecture

```
src/weconnect_mcp/
├── adapter/
│   ├── abstract_adapter.py       # AbstractAdapter (ABC) + Pydantic models — the port
│   ├── tibber_adapter.py         # TibberAdapter — the only concrete adapter
│   ├── starting_adapter.py       # No-op stub used during async startup (HTTP mode)
│   ├── tibber_client.py          # TibberDataAPI: OAuth2 (Auth Code + PKCE) client
│   └── mixins/
│       ├── cache_mixin.py                  # 5-min data cache
│       ├── vehicle_resolution_mixin.py     # VIN/name/license-plate → VIN resolution
│       └── tibber_state_extraction_mixin.py # Extract charging/range from Tibber's response
├── server/
│   ├── mcp_server.py             # get_server() — builds the FastMCP instance
│   ├── AI_INSTRUCTIONS.md        # Canonical AI-facing tool description — keep in sync!
│   └── mixins/
│       ├── read_tools.py         # The 5 MCP tools (only registration left besides prompts)
│       └── prompts.py            # 11 MCP workflow prompts
└── cli/
    ├── mcp_server_cli.py         # Entry point: weconnect_mcp.cli.mcp_server_cli
    ├── tibber_login_cli.py       # One-time interactive OAuth2 login
    └── logging_config.py         # Central logging setup
```

`AbstractAdapter` only declares what Tibber can actually back: `list_vehicles`,
`get_vehicle`, `get_energy_status`, `shutdown`, plus concrete defaults
`resolve_vehicle_id`/`invalidate_cache`. There is **no** MCP Resources layer
(deliberately removed — a 1:1 duplicate of the tools with no benefit for the
clients this targets) and **no** command/write tools (Tibber's API has no
write endpoints at all).

### MCP surface (keep README.md and AI_INSTRUCTIONS.md in sync with this)

5 tools, all fully functional (no "registered but always fails" tools exist):
`get_vehicles`, `get_vehicle_info`, `get_vehicle_state`, `get_battery_status`,
`get_charging_status`. Plus 11 workflow prompts in `prompts.py`.

**Whenever you add/remove/rename a tool or prompt, update all three:**
`README.md` (AI Integration section), `AI_INSTRUCTIONS.md`, and the
registration file itself.

## Coding conventions

- **Type hints required** on all function parameters and return values.
- **Naming**: `snake_case.py` files, `PascalCase` classes, `snake_case()`
  functions/methods, `UPPER_SNAKE_CASE` constants.
- **Imports**: standard library → third-party → local.
- **None handling**: Tibber only reports a handful of fields and many are
  `None` by design (not an error) — always check before use, don't assume a
  field is populated.
- **Docstrings**: Google-style; document *why*, not *what* — see the
  top-level system prompt's comment guidance (comments only for non-obvious
  constraints/invariants, not restating the code).
- **Mixin pattern**: adapters and server registration are composed from
  single-responsibility mixins (see Architecture above). Follow this pattern
  for new cross-cutting concerns rather than adding methods directly to
  `TibberAdapter`.

## Testing

```bash
./scripts/test.sh          # whole suite, ~0.1s, no credentials needed
./scripts/test.sh -v       # verbose
```

36 tests total, all against `tests/test_adapter.py`'s `TestAdapter` mock (2
fake vehicles: electric ID.7 Tourer, combustion Transporter 7 — see that
file's docstring for exact values). No slow/real-API test suite exists: the
Tibber Data API is read-only, so the mock adapter already covers everything
the real API could return. See `tests/README.md` for full structure.

**All 36 tests must pass before committing.** When adding a tool, add tests
under `tests/tools/test_<name>.py` following the existing pattern (success
case, vehicle-not-found case, edge cases).

## Running locally

```bash
./scripts/setup.sh                          # create venv, install editable
cp src/tibber_config.example.json src/tibber_config.json
# edit src/tibber_config.json with your Tibber OAuth2 client_id/secret
python -m weconnect_mcp.cli.tibber_login_cli src/tibber_config.json   # one-time login
./scripts/start_server_fg.sh                # foreground, console logs
```

`src/tibber_config.json` is gitignored (real credentials) — never commit it.
Register an OAuth2 client at <https://data-api.tibber.com/clients/manage/>.

## Key docs to check before changing behavior

- `README.md` — user-facing setup, deployment, AI Integration tool list
- `src/weconnect_mcp/server/AI_INSTRUCTIONS.md` — canonical AI-facing tool
  description (what a client-side AI assistant is told about this server)
- `experiment/tibber-integration/TIBBER_API.md` — full Tibber API research,
  architecture rationale, and an append-only session log of prior work on
  this project (read the tail before starting new work; append, don't
  rewrite, when you finish something notable)
- `CONTRIBUTING.md` — contribution guidelines, code style detail

## Working with the user

- Prefers **live verification** over static claims — run it, don't just
  read the code and assume it works.
- Wants to be **asked before risky/ambiguous decisions**, not have them
  made silently (e.g. whether to delete a file with real credentials,
  whether to enable/remove a disabled feature).
- Wants **findings surfaced, not silently fixed**, when something looks
  like a pre-existing bug outside the current task's scope.
- Git commits on feature branches follow Conventional Commits
  (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`), with a `!` suffix for
  interface-breaking changes, and a detailed body explaining *why*.
