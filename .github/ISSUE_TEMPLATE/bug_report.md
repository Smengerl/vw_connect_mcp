---
name: Bug Report
about: Report a bug or unexpected behavior
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
A clear and concise description of what the bug is.

## Steps to Reproduce
1. Run command '...'
2. With configuration '...'
3. See error

## Expected Behavior
A clear description of what you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- **OS:** [e.g. macOS 14.2, Ubuntu 22.04]
- **Python version:** [e.g. 3.11.5]
- **Installation method:** [e.g. from source, pip]
- **Vehicle type:** [e.g. ID.7 BEV, Golf PHEV]

## Configuration (sanitized)
```json
{
  "client_id": "...",
  "redirect_uri": "http://localhost:8515/callback",
  "token_path": "./tibber_tokens.json"
}
```
**Note:** Remove sensitive data like `client_secret` and token contents!

## Logs
If applicable, add logs from:
```bash
# Run with debug logging
python -m weconnect_mcp.cli.mcp_server_cli src/tibber_config.json --log-level DEBUG --log-file debug.log
```

<details>
<summary>Click to expand logs</summary>

```
Paste logs here
```

</details>

## Additional Context
Add any other context about the problem here (screenshots, related issues, etc.)
