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

# Writable directory for token persistence, owned by mcpuser before any
# volume gets mounted over it (Docker/Railway copy this ownership onto a
# freshly-mounted empty volume, so this must happen before USER below).
# TIBBER_TOKEN_PATH defaults into this directory below.
RUN mkdir -p /tmp/tibber-tokens && chown -R mcpuser /tmp

USER mcpuser

# Credentials: TIBBER_CLIENT_ID/TIBBER_CLIENT_SECRET, plus a token file at
# TIBBER_TOKEN_PATH (defaulted below to the tibber-tokens volume mounted in
# docker-compose.yml). Tibber has no client_credentials grant (confirmed
# live, experiment/tibber-integration/TIBBER_API.md §3.4) -- a
# refresh_token must persist across restarts one way or another, and the
# interactive login that produces one cannot run inside a headless
# container. Bootstrap it with TIBBER_TOKEN_JSON: run
# `python -m weconnect_mcp.cli.tibber_login_cli` once LOCALLY, then paste
# that run's token file contents into TIBBER_TOKEN_JSON (as a Railway
# variable, docker-compose environment entry, or `docker run -e`).
# _seed_tibber_token_from_env() in mcp_server_cli.py writes it to
# TIBBER_TOKEN_PATH once, on first boot only, if no file exists there yet
# -- every refresh after that rewrites the file (including Tibber's
# rotating refresh_token) and, as long as TIBBER_TOKEN_PATH is on a
# persisted volume, survives future restarts without the stale env var
# ever being read again.
ENV MCP_API_KEY=""
ENV TIBBER_CLIENT_ID=""
ENV TIBBER_CLIENT_SECRET=""
ENV TIBBER_TOKEN_JSON=""
ENV TIBBER_TOKEN_PATH=/tmp/tibber-tokens/tibber_tokens.json
# Default port for Railway (Railway injects its own PORT env var at runtime).
# For local Docker, the host-side mapping in docker-compose.yml maps the
# external port 8089 to this internal container port 8080.
ENV PORT=8080

# Health-check: the /health endpoint is added in mcp_server.py (Stufe 1)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen(f'http://localhost:{PORT}/health')" || exit 1

EXPOSE $PORT

# Shell form so that $PORT is expanded at runtime.
# Railway injects PORT automatically; default in image is 8080.
# Local Docker users access the server via the host port (8089) defined in docker-compose.yml.
CMD python -m weconnect_mcp.cli.mcp_server_cli \
    --transport http \
    --port "$PORT" \
    --log-level INFO
