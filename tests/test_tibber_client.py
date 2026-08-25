"""
Tests for tibber_client.py's token-refresh locking and reauth handling
========================================================================

Covers the concurrent-instance token refresh coordination described in
ARCHITECTURE.md §2.4: multiple server instances can share one token file
(same machine only), and Tibber rotates refresh tokens on every successful
refresh.

Two tiers of coverage here:

- Most tests below simulate "another instance already did X" by writing to
  the file *before* calling `_refresh()` -- sequential, single-threaded,
  fast. This exercises the re-read-under-lock logic itself (adopt if
  fresh, bail out if already cleared) without needing real concurrency.
- The `test_refresh_concurrent_*` tests at the bottom use real threads and
  a `threading.Barrier` to make two `_refresh()` calls genuinely overlap
  and contend for the actual OS `flock` at the same instant -- this is
  the only tier that would catch a regression in the locking itself (e.g.
  someone "simplifying" `TokenStore.locked()` in a way that stops
  serializing callers). POSIX `flock()` locks are per open-file-description
  (not per-process, unlike `fcntl.lockf`'s record locks), so this
  genuinely contends even within one test process/thread pool.

TibberAuthError has no per-code subclasses (see its own docstring) --
every test below checks `error_type` on the base class instead of
`pytest.raises` on a specific subclass.

No real network calls: httpx.post is mocked via unittest.mock.patch.
"""
import json
import sys
import threading
import time
from unittest.mock import patch, Mock

import pytest

from weconnect_mcp.adapter.tibber_client import (
    TibberAuthError,
    TibberDataAPI,
    TibberTokenEndpointError,
    TokenSet,
    TokenStore,
    default_login_command,
    login_instruction,
)


def _make_client(store: TokenStore) -> TibberDataAPI:
    return TibberDataAPI(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="http://localhost:8515/callback",
        store=store,
    )


def _token(*, expired: bool, refresh_token: str | None = "refresh-1") -> TokenSet:
    offset = -100.0 if expired else 3600.0
    return TokenSet(
        access_token="access-1",
        refresh_token=refresh_token,
        expires_at=time.time() + offset,
    )


def _fake_response(status_code: int, body: dict) -> Mock:
    resp = Mock()
    resp.status_code = status_code
    resp.text = json.dumps(body)
    resp.json.return_value = body
    return resp


# ==================== TibberTokenEndpointError classification ====================

@pytest.mark.parametrize(
    "status_code,body,expected",
    [
        (400, '{"error":"invalid_grant"}', False),
        (400, '{"error":"invalid_client"}', True),
        (400, '{"error":"unauthorized_client"}', True),
        (400, '{"error":"unsupported_grant_type"}', False),
        (500, '{"error":"invalid_client"}', False),
        (400, "not json", False),
    ],
)
def test_is_invalid_client(status_code, body, expected):
    exc = TibberTokenEndpointError(status_code, body)
    assert exc.is_invalid_client is expected


@pytest.mark.parametrize(
    "status_code,body,expected",
    [
        (400, '{"error":"invalid_grant"}', True),
        (400, '{"error":"invalid_client"}', False),
        (400, '{"error":"unauthorized_client"}', False),
        (400, '{"error":"unsupported_grant_type"}', False),
        (500, '{"error":"invalid_grant"}', False),
        (400, "not json", False),
    ],
)
def test_is_invalid_grant(status_code, body, expected):
    exc = TibberTokenEndpointError(status_code, body)
    assert exc.is_invalid_grant is expected


# ==================== default_login_command() / login_instruction() ====================

def test_default_login_command_uses_this_interpreter():
    """Must use sys.executable, not a bare `python`/`python3` or the
    installed `weconnect-tibber-login` console script name -- both of
    those only work if the right venv happens to already be active and on
    PATH in whatever shell runs the command, which a human copy-pasting
    from a chat (or an MCP client's own environment) generally isn't."""
    cmd = default_login_command()
    assert cmd == f"{sys.executable} -m weconnect_mcp.cli.tibber_login_cli"


def test_default_login_command_includes_config_path_when_given():
    cmd = default_login_command("/some/path/tibber_config.json")
    assert cmd == f"{sys.executable} -m weconnect_mcp.cli.tibber_login_cli /some/path/tibber_config.json"


def test_login_instruction_uses_exact_command_outside_a_container(monkeypatch):
    # Force the "not in a container" branch regardless of the host actually
    # running this test.
    monkeypatch.setattr("weconnect_mcp.adapter.tibber_client._running_in_container", lambda: False)
    instruction = login_instruction("/venv/bin/python -m weconnect_mcp.cli.tibber_login_cli")
    assert "/venv/bin/python -m weconnect_mcp.cli.tibber_login_cli" in instruction
    assert "server host" in instruction


def test_login_instruction_warns_about_container_instead_of_naming_a_broken_path(monkeypatch):
    """Inside a container, sys.executable only names a path valid inside
    that container -- the instruction must not tell the reader to run it,
    since it can't work there (no browser) or on their own machine (the
    path doesn't exist there either)."""
    monkeypatch.setattr("weconnect_mcp.adapter.tibber_client._running_in_container", lambda: True)
    instruction = login_instruction("/usr/local/bin/python3.12 -m weconnect_mcp.cli.tibber_login_cli")
    assert "/usr/local/bin/python3.12" not in instruction
    assert "container" in instruction
    assert "TIBBER_TOKEN_JSON" in instruction


def test_running_in_container_detects_dockerenv(monkeypatch):
    from weconnect_mcp.adapter.tibber_client import _running_in_container

    monkeypatch.setattr("os.path.exists", lambda path: path == "/.dockerenv")
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    assert _running_in_container() is True


def test_running_in_container_detects_railway_env_var(monkeypatch):
    from weconnect_mcp.adapter.tibber_client import _running_in_container

    monkeypatch.setattr("os.path.exists", lambda path: False)
    monkeypatch.setenv("RAILWAY_PROJECT_ID", "some-id")
    assert _running_in_container() is True


def test_running_in_container_false_locally(monkeypatch):
    from weconnect_mcp.adapter.tibber_client import _running_in_container

    monkeypatch.setattr("os.path.exists", lambda path: False)
    for key in list(__import__("os").environ):
        if key.startswith("RAILWAY_"):
            monkeypatch.delenv(key, raising=False)
    assert _running_in_container() is False


# ==================== ensure_authorized() with no cached tokens ====================

def test_ensure_authorized_with_no_cached_tokens_raises_reauth_required(tmp_path):
    """No token file at all (login never run) and interactive login
    disabled (as inside the MCP server process) must raise a
    TibberAuthError with error_type "reauth_required" -- distinguishable
    from a not-configured or invalid-client-credentials problem, and with
    the same fix (run the login tool) as an actually-expired refresh
    token."""
    client = _make_client(TokenStore(tmp_path / "tokens.json"))

    with pytest.raises(TibberAuthError) as exc_info:
        client.ensure_authorized()

    assert exc_info.value.error_type == "reauth_required"


def test_ensure_authorized_message_includes_the_given_login_command(tmp_path):
    """The exact login_command passed in (as mcp_server_cli._build_tibber_adapter
    does, using the real credentials-file path) must appear verbatim in the
    error message an MCP client/AI assistant sees -- not a generic,
    possibly-wrong hint."""
    client = TibberDataAPI(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="http://localhost:8515/callback",
        store=TokenStore(tmp_path / "tokens.json"),
        login_command="/venv/bin/python -m weconnect_mcp.cli.tibber_login_cli /my/config.json",
    )

    with pytest.raises(TibberAuthError) as exc_info:
        client.ensure_authorized()

    assert "/venv/bin/python -m weconnect_mcp.cli.tibber_login_cli /my/config.json" in str(exc_info.value)


# ==================== _refresh() coordination ====================

def test_refresh_adopts_peer_refreshed_token_without_network_call(tmp_path):
    path = tmp_path / "tokens.json"
    store1 = TokenStore(path)
    store1.save(_token(expired=True))
    client1 = _make_client(store1)

    # Simulate a peer instance having already refreshed while we waited.
    fresh = _token(expired=False)
    TokenStore(path).save(fresh)

    with patch("weconnect_mcp.adapter.tibber_client.httpx.post") as mock_post:
        client1._refresh()

    mock_post.assert_not_called()
    assert client1.tokens.access_token == fresh.access_token


def test_refresh_raises_reauth_required_when_peer_already_cleared(tmp_path):
    path = tmp_path / "tokens.json"
    store1 = TokenStore(path)
    store1.save(_token(expired=True))
    client1 = _make_client(store1)

    # Simulate a peer instance having already confirmed the refresh token
    # is dead and cleared the file.
    TokenStore(path).clear()

    with patch("weconnect_mcp.adapter.tibber_client.httpx.post") as mock_post:
        with pytest.raises(TibberAuthError) as exc_info:
            client1._refresh()

    assert exc_info.value.error_type == "reauth_required"
    mock_post.assert_not_called()
    assert client1.tokens is None


def test_refresh_clears_store_on_invalid_grant(tmp_path):
    path = tmp_path / "tokens.json"
    store = TokenStore(path)
    store.save(_token(expired=True))
    client = _make_client(store)

    with patch("weconnect_mcp.adapter.tibber_client.httpx.post") as mock_post:
        mock_post.return_value = _fake_response(400, {"error": "invalid_grant"})
        with pytest.raises(TibberAuthError) as exc_info:
            client._refresh()

    assert exc_info.value.error_type == "reauth_required"
    assert client.tokens is None
    assert TokenStore(path).load() is None


def test_refresh_clears_store_on_unrecognized_400_error_code(tmp_path):
    """A 400 response is a client-side rejection by definition (OAuth2/HTTP
    semantics), never something a blind retry fixes -- even when the
    specific `error` code isn't one of the two this project recognizes by
    name. It must be treated the same as a confirmed invalid_grant
    (reauth_required, store cleared) rather than silently falling into the
    generic "unavailable, just retry" bucket meant for actually-transient
    failures (5xx, rate limiting)."""
    path = tmp_path / "tokens.json"
    store = TokenStore(path)
    store.save(_token(expired=True))
    client = _make_client(store)

    with patch("weconnect_mcp.adapter.tibber_client.httpx.post") as mock_post:
        mock_post.return_value = _fake_response(400, {"error": "invalid_scope"})
        with pytest.raises(TibberAuthError) as exc_info:
            client._refresh()

    assert exc_info.value.error_type == "reauth_required"
    assert TokenStore(path).load() is None


def test_refresh_leaves_store_on_transient_error(tmp_path):
    path = tmp_path / "tokens.json"
    store = TokenStore(path)
    stale = _token(expired=True)
    store.save(stale)
    client = _make_client(store)

    with patch("weconnect_mcp.adapter.tibber_client.httpx.post") as mock_post:
        mock_post.return_value = _fake_response(500, {"error": "server_error"})
        with pytest.raises(TibberTokenEndpointError) as exc_info:
            client._refresh()

    assert exc_info.value.is_invalid_client is False
    assert exc_info.value.is_invalid_grant is False
    assert exc_info.value.error_type == "unavailable"
    # Store untouched -- worth retrying later against the same refresh token.
    reloaded = TokenStore(path).load()
    assert reloaded is not None
    assert reloaded.refresh_token == stale.refresh_token


def test_refresh_raises_client_invalid_without_clearing_store_on_invalid_client(tmp_path):
    """invalid_client/unauthorized_client means the client_id/secret
    themselves are rejected -- a distinct, differently-fixed problem from
    an expired refresh token (test_refresh_clears_store_on_invalid_grant
    above), so it must raise error_type "invalid_client", not
    "reauth_required", and must not clear the token file (the
    refresh_token itself may still be perfectly good)."""
    path = tmp_path / "tokens.json"
    store = TokenStore(path)
    stale = _token(expired=True)
    store.save(stale)
    client = _make_client(store)

    with patch("weconnect_mcp.adapter.tibber_client.httpx.post") as mock_post:
        mock_post.return_value = _fake_response(400, {"error": "invalid_client"})
        with pytest.raises(TibberAuthError) as exc_info:
            client._refresh()

    assert exc_info.value.error_type == "invalid_client"
    reloaded = TokenStore(path).load()
    assert reloaded is not None
    assert reloaded.refresh_token == stale.refresh_token


def test_token_request_wraps_network_failure(tmp_path):
    """A connection-level failure (DNS, refused, timeout) reaching Tibber's
    token endpoint is a transient connectivity problem, not a credentials
    problem -- it must surface as error_type "network_error", distinct
    from both "invalid_client" and "reauth_required", so the MCP client
    doesn't get told to re-authorize when the real issue is that the
    server couldn't reach Tibber at all."""
    import httpx

    path = tmp_path / "tokens.json"
    store = TokenStore(path)
    store.save(_token(expired=True))
    client = _make_client(store)

    with patch("weconnect_mcp.adapter.tibber_client.httpx.post", side_effect=httpx.ConnectError("nope")):
        with pytest.raises(TibberAuthError) as exc_info:
            client._refresh()

    assert exc_info.value.error_type == "network_error"
    # Store untouched -- this isn't a rejection, just unreachable right now.
    assert TokenStore(path).load() is not None


def test_get_wraps_network_failure(tmp_path):
    """The same network_error translation _refresh()/_token_request() has
    must also apply to plain data-fetch calls (homes/devices/device) --
    not just the token endpoint. Before this, an httpx failure here
    propagated as a raw, unclassified exception instead of the clean
    server_unavailable JSON every other failure mode produces."""
    import httpx

    path = tmp_path / "tokens.json"
    store = TokenStore(path)
    store.save(_token(expired=False))
    client = _make_client(store)

    with patch("weconnect_mcp.adapter.tibber_client.httpx.get", side_effect=httpx.ConnectError("nope")):
        with pytest.raises(TibberAuthError) as exc_info:
            client.homes()

    assert exc_info.value.error_type == "network_error"


def test_get_wraps_unexpected_status_error(tmp_path):
    """A non-401 error status (e.g. a Tibber-side 500) from a data-fetch
    call must also be classified, not left to raise_for_status()'s raw
    httpx.HTTPStatusError uncaught."""
    path = tmp_path / "tokens.json"
    store = TokenStore(path)
    store.save(_token(expired=False))
    client = _make_client(store)

    bad_resp = _fake_response(500, {"error": "server_error"})
    bad_resp.raise_for_status.side_effect = __import__("httpx").HTTPStatusError(
        "500", request=Mock(), response=bad_resp
    )

    with patch("weconnect_mcp.adapter.tibber_client.httpx.get", return_value=bad_resp):
        with pytest.raises(TibberAuthError) as exc_info:
            client.homes()

    assert exc_info.value.error_type == "network_error"


def test_refresh_success_persists_rotated_token(tmp_path):
    path = tmp_path / "tokens.json"
    store = TokenStore(path)
    store.save(_token(expired=True, refresh_token="old-refresh"))
    client = _make_client(store)

    with patch("weconnect_mcp.adapter.tibber_client.httpx.post") as mock_post:
        mock_post.return_value = _fake_response(200, {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "openid",
        })
        client._refresh()

    assert client.tokens.access_token == "new-access"
    reloaded = TokenStore(path).load()
    assert reloaded.access_token == "new-access"
    assert reloaded.refresh_token == "new-refresh"


def test_refresh_without_refresh_token_and_no_interactive_login_raises(tmp_path):
    path = tmp_path / "tokens.json"
    store = TokenStore(path)
    store.save(_token(expired=True, refresh_token=None))
    client = _make_client(store)

    with patch("weconnect_mcp.adapter.tibber_client.httpx.post") as mock_post:
        with pytest.raises(TibberAuthError) as exc_info:
            client._refresh()

    # error_type must be "reauth_required" -- the fix is the same as a
    # rejected refresh token (re-run the login tool), even though the
    # underlying cause (never had a refresh_token at all) differs.
    assert exc_info.value.error_type == "reauth_required"
    mock_post.assert_not_called()


# ==================== Real concurrency: two threads, one flock ====================

def test_refresh_concurrent_threads_only_one_network_call(tmp_path):
    """Two independent TibberDataAPI instances, two threads, released at
    the same instant via a Barrier -- genuine contention on the real
    flock, not a scripted sequence. Whichever thread wins refreshes once;
    the other must adopt that result via the lock's re-read instead of
    also hitting the (mocked) token endpoint -- exactly the scenario that
    originally broke live with two real server processes.
    """
    path = tmp_path / "tokens.json"
    store = TokenStore(path)
    store.save(_token(expired=True, refresh_token="shared-refresh"))

    client_a = _make_client(TokenStore(path))
    client_b = _make_client(TokenStore(path))

    call_count = 0
    count_lock = threading.Lock()

    def slow_token_request(*args, **kwargs):
        nonlocal call_count
        with count_lock:
            call_count += 1
        time.sleep(0.05)  # widen the window so a broken lock would double-call
        return _fake_response(200, {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "expires_in": 3600,
        })

    barrier = threading.Barrier(2)
    errors: list[Exception] = []

    def run(client: TibberDataAPI) -> None:
        try:
            barrier.wait(timeout=5)
            client._refresh()
        except Exception as exc:  # noqa: BLE001 -- collected, not raised, from a thread
            errors.append(exc)

    with patch("weconnect_mcp.adapter.tibber_client.httpx.post", side_effect=slow_token_request):
        t1 = threading.Thread(target=run, args=(client_a,))
        t2 = threading.Thread(target=run, args=(client_b,))
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

    assert errors == []
    assert call_count == 1
    assert client_a.tokens.access_token == "new-access"
    assert client_b.tokens.access_token == "new-access"


def test_refresh_concurrent_threads_dead_token_only_one_network_call(tmp_path):
    """Same real-concurrency setup, but Tibber rejects the shared refresh
    token: only one thread should actually call the (mocked) token
    endpoint; the other must see the cleared file via the lock's re-read
    and raise a reauth_required TibberAuthError without a second network
    call.
    """
    path = tmp_path / "tokens.json"
    store = TokenStore(path)
    store.save(_token(expired=True, refresh_token="dead-refresh"))

    client_a = _make_client(TokenStore(path))
    client_b = _make_client(TokenStore(path))

    call_count = 0
    count_lock = threading.Lock()

    def slow_reject(*args, **kwargs):
        nonlocal call_count
        with count_lock:
            call_count += 1
        time.sleep(0.05)
        return _fake_response(400, {"error": "invalid_grant"})

    barrier = threading.Barrier(2)
    outcomes: dict[str, str] = {}

    def run(name: str, client: TibberDataAPI) -> None:
        try:
            barrier.wait(timeout=5)
            client._refresh()
            outcomes[name] = "no error (unexpected)"
        except TibberAuthError as exc:
            outcomes[name] = exc.error_type
        except Exception as exc:  # noqa: BLE001
            outcomes[name] = f"unexpected: {exc!r}"

    with patch("weconnect_mcp.adapter.tibber_client.httpx.post", side_effect=slow_reject):
        t1 = threading.Thread(target=run, args=("a", client_a))
        t2 = threading.Thread(target=run, args=("b", client_b))
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

    assert call_count == 1
    assert outcomes == {"a": "reauth_required", "b": "reauth_required"}
    assert TokenStore(path).load() is None
