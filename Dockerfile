# ── Stage 1: build / install dependencies ────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install only what's needed for pip to build native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir --prefix=/install .


# ── Stage 2: lean runtime image ──────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="WeConnect MCP Server"
LABEL org.opencontainers.image.description="MCP server for Volkswagen WeConnect vehicle data and control"
LABEL org.opencontainers.image.source="https://github.com/Smengerl/weconnect_mvp"

# Create unprivileged user for security
RUN useradd --system --no-create-home --shell /usr/sbin/nologin mcpuser

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY src/ ./src/

# Writable directory for token store (carconnectivity caches OAuth tokens here).
# The CLI passes /tmp/tokenstore as a FILE PREFIX, not a directory.
RUN mkdir -p /tmp && chown mcpuser /tmp

USER mcpuser

# Backend selection -- 'tibber' (default, works today) or 'carconnectivity'
# (VW-direct, currently blocked by VW, see README.md warning). Overridable at
# container RUNTIME (docker run -e MCP_BACKEND=carconnectivity, a Railway
# variable, or docker-compose's `environment:`) -- no image rebuild needed,
# same as every other credential below.
ENV MCP_BACKEND=tibber

# carconnectivity backend: VW_USERNAME/VW_PASSWORD/VW_SPIN (or bake a real
#   config.json into your own image build instead).
# tibber backend (default): TIBBER_CLIENT_ID/TIBBER_CLIENT_SECRET, plus a
#   TIBBER_TOKEN_PATH pointing at a pre-existing token file. That file must
#   be produced by a one-time LOCAL interactive login (`python -m
#   weconnect_mcp.cli.tibber_login_cli`, see experiment/tibber-integration/
#   README.md) -- the login itself cannot run inside a headless container.
#   Verified working: `docker run ... -e TIBBER_TOKEN_PATH=/tmp/tokens/x.json
#   -v /path/to/local/tokens:/tmp/tokens ...` (manual bind mount). No named
#   volume + documented workflow for this exists in docker-compose.yml yet
#   (unlike carconnectivity's `tokenstore` volume) -- tracked as a follow-up.
ENV MCP_API_KEY=""
ENV VW_USERNAME=""
ENV VW_PASSWORD=""
ENV VW_SPIN=""
# Default port for Railway (Railway injects its own PORT env var at runtime).
# For local Docker, the host-side mapping in docker-compose.yml maps the
# external port 8089 to this internal container port 8080.
ENV PORT=8080

# Health-check: the /health endpoint is added in mcp_server.py (Stufe 1)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen(f'http://localhost:{PORT}/health')" || exit 1

EXPOSE $PORT

# Minimal config stub for the carconnectivity backend (real credentials come
# from VW_* env vars via _maybe_patch_config_from_env() in mcp_server_cli.py).
# Harmless no-op for the default tibber backend: _build_tibber_adapter()
# ignores a config file with no matching client_id/client_secret keys and
# falls back to TIBBER_* env vars.
COPY src/config.example.json /app/config.json

# Shell form so that $PORT/$MCP_BACKEND are expanded at runtime.
# Railway injects PORT automatically; default in image is 8080.
# Local Docker users access the server via the host port (8089) defined in docker-compose.yml.
CMD python -m weconnect_mcp.cli.mcp_server_cli \
    /app/config.json \
    --backend "$MCP_BACKEND" \
    --transport http \
    --port "$PORT" \
    --tokenstorefile /tmp/ts/token \
    --log-level INFO
