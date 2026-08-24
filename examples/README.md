# Examples

This directory contains demonstration scripts showcasing the capabilities of the weconnect_mvp MCP server (Tibber Data API backend).

## Quick Start

Run any example with:
```bash
python3 examples/<example_name>.py
```

## Available Examples

### `vehicle_identifier_demo.py`
Shows the flexible vehicle identification system.

**What it demonstrates:**
- Identify vehicles by VIN, name, or license plate
- Case-insensitive matching
- Resolution priority: Name > VIN > License Plate
- Energy status lookup with different identifiers
- All three methods return identical results

**Example identifiers:**
- `'ID7'` - by name
- `'WVWZZZED4SE003938'` - by VIN
- `'M-XY 5678'` - by license plate

```bash
python3 examples/vehicle_identifier_demo.py
```

---

### `license_plate_demo.py`
Demonstrates the license plate support in `VehicleModel` and `VehicleListItem`.

**What it shows:**
- License plates in `list_vehicles()` and `get_vehicle()`
- Vehicle identification by license plate
- Consistency check between methods
- Practical use cases (user-friendly selection, fleet management)

**Note:** with the Tibber backend, `license_plate` is always `None` in
practice — Tibber's Data API doesn't provide it. `TestAdapter`'s mock data
includes plates purely to illustrate the field and the resolution logic.

```bash
python3 examples/license_plate_demo.py
```

---

### `caching_demo.py`
Explains the caching system that avoids hammering the Tibber Data API.

**What it shows:**
- Cache configuration (default: 300 seconds / 5 minutes)
- Cache behavior (hit/miss)
- Internal mechanism (`CacheMixin`)
- Customization guide
- Logging examples

**Key features:**
- ✅ Automatic caching of Tibber API responses
- ✅ Configurable duration via `CACHE_DURATION_SECONDS` in `tibber_adapter.py`
- ✅ Transparent to users (no code changes needed)

```bash
python3 examples/caching_demo.py
```

---

## Test Data

All examples use the `TestAdapter` (from `tests/test_adapter.py`), which provides mock data:

**Vehicle 1: T7 (Transporter 7)**
- VIN: `WV2ZZZSTZNH009136`
- Type: Combustion
- License Plate: `M-AB 1234`

**Vehicle 2: ID7 (ID.7 Tourer)**
- VIN: `WVWZZZED4SE003938`
- Type: Electric
- License Plate: `M-XY 5678`

---

## Running with Real Data

To use your real vehicle instead of test data, replace `TestAdapter()` with `TibberAdapter`:

```python
from weconnect_mcp.adapter.tibber_adapter import TibberAdapter

adapter = TibberAdapter(
    client_id="...",
    client_secret="...",
    redirect_uri="http://localhost:8515/callback",
    token_path="tibber_tokens.json",
)
```

This requires a one-time interactive login first — run
`python -m weconnect_mcp.cli.tibber_login_cli` to produce the token file at
`token_path`. See the root [README.md](../README.md) for the full setup
(registering an OAuth2 client, environment variables vs. a credentials
file). Caching (see `caching_demo.py`) already keeps repeated calls
polite towards Tibber's API — no extra rate-limit handling needed.

---

## Contributing

When adding new examples:

1. **Use descriptive names:** `<feature>_demo.py`
2. **Include docstring:** Explain what the demo shows
3. **Add print statements:** Make output clear and formatted
4. **Use TestAdapter:** For consistent test data
5. **Update this README:** Add your example to the list

---

## Questions?

- Check the main [README.md](../README.md) for project overview
- See [tests/README.md](../tests/README.md) for testing documentation
- Review [AI_INSTRUCTIONS.md](../src/weconnect_mcp/server/AI_INSTRUCTIONS.md) for MCP tool usage
