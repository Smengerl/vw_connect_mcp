"""
Tests for the /health endpoint (mcp_server.py)
=================================================

Covers the differentiated readiness reporting: /health must be able to
tell "connected fine" apart from "gave up, backend unavailable", including
through the ReconnectingAdapter layer mcp_server_cli.py wraps the
real/fallback adapter in for both transports (see ARCHITECTURE.md §2.4 and
starting_adapter.py's ReconnectingAdapter). There is no separate "still
starting" state any more -- both transports connect synchronously before
serving a single request, so by the time /health is reachable, the backend
has already been resolved one way or the other.

Hits the route directly via an ASGI transport (no real HTTP socket) --
fast and matches this suite's offline unit-test style.
"""
import httpx
import pytest

from weconnect_mcp.adapter.starting_adapter import ReconnectingAdapter, UnavailableAdapter
from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter
from weconnect_mcp.server.mcp_server import get_server


class _FakeWorkingAdapter(AbstractAdapter):
    def list_vehicles(self): return []
    def get_vehicle(self, vehicle_id, details=None): return None
    def get_energy_status(self, vehicle_id): return None
    def shutdown(self): pass


async def _get_health(adapter) -> dict:
    server = get_server(adapter)
    app = server.http_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with app.router.lifespan_context(app):
            resp = await client.get("/health")
    return resp.json()


@pytest.mark.asyncio
async def test_health_reports_ok_when_connected():
    body = await _get_health(_FakeWorkingAdapter())
    assert body == {"status": "ok", "service": "weconnect-mcp", "ready": True}


@pytest.mark.asyncio
async def test_health_reports_unavailable_through_reconnecting_adapter():
    """The real deployment shape: the adapter passed to get_server() is a
    ReconnectingAdapter wrapping UnavailableAdapter. The health route must
    unwrap that layer to surface error_type/message, not just report a
    bare "ready": true."""
    unavailable = UnavailableAdapter("still not configured", error_type="not_configured")
    reconnecting = ReconnectingAdapter(build=lambda: unavailable, initial=unavailable)

    body = await _get_health(reconnecting)

    assert body == {
        "status": "unavailable",
        "service": "weconnect-mcp",
        "ready": False,
        "error_type": "not_configured",
        "message": "still not configured",
    }


@pytest.mark.asyncio
async def test_health_reports_ok_through_reconnecting_adapter_once_healed():
    healed = _FakeWorkingAdapter()
    reconnecting = ReconnectingAdapter(build=lambda: healed, initial=healed)

    body = await _get_health(reconnecting)

    assert body == {"status": "ok", "service": "weconnect-mcp", "ready": True}


@pytest.mark.asyncio
async def test_health_probe_itself_triggers_the_heal_without_any_tool_call():
    """A passive GET /health must not just report a stale state forever --
    it must attempt the same reconnect a real tool call would (subject to
    the same cooldown), so an orchestrator relying purely on /health for
    readiness (exactly how Dockerfile/docker-compose.yml/railway.toml wire
    it) doesn't keep a service out of rotation after a human already fixed
    the problem but no MCP tool client has reconnected yet."""
    import time

    unavailable = UnavailableAdapter("still broken", error_type="not_configured")
    healed = _FakeWorkingAdapter()
    reconnecting = ReconnectingAdapter(build=lambda: healed, initial=unavailable)
    reconnecting._last_attempt = time.monotonic() - 9999.0  # cooldown long elapsed

    body = await _get_health(reconnecting)

    assert body == {"status": "ok", "service": "weconnect-mcp", "ready": True}
