# ── Stage 1: build / install dependencies ────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install only what's needed for pip to build native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


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

# Make the src/ directory importable as a Python package root
ENV PYTHONPATH=/app/src

# Writable directory for token store (carconnectivity caches OAuth tokens here).
# The CLI passes /tmp/tokenstore as a FILE PREFIX, not a directory.
RUN mkdir -p /tmp && chown mcpuser /tmp

USER mcpuser

# MCP_API_KEY, VW_USERNAME, VW_PASSWORD, VW_SPIN must be set at runtime.
# config.json is optional when env variables are set; mount via secret if needed.
ENV MCP_API_KEY=""
ENV VW_USERNAME=""
ENV VW_PASSWORD=""
ENV VW_SPIN=""
ENV PORT=8080

# Health-check: the /health endpoint is added in mcp_server.py (Stufe 1)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen(f'http://localhost:{PORT}/health')" || exit 1

EXPOSE $PORT

# Use a minimal config stub – real credentials come from env variables via
# _maybe_patch_config_from_env() in mcp_server_cli.py
COPY src/config.example.json /app/config.json

# Shell form so that $PORT is expanded at runtime.
# Railway injects PORT automatically; locally it defaults to 8080.
CMD python -m weconnect_mcp.cli.mcp_server_cli \
    /app/config.json \
    --transport http \
    --port "${PORT:-8080}" \
    --log-level INFO
