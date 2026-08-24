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

No real network calls: httpx.post is mocked via unittest.mock.patch.
"""
import json
import threading
import time
from unittest.mock import patch, Mock

import pytest

from weconnect_mcp.adapter.tibber_client import (
    TibberAuthError,
    TibberDataAPI,
    TibberReauthRequiredError,
    TibberTokenEndpointError,
    TokenSet,
    TokenStore,
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


# ==================== TibberTokenEndpointError.is_reauth_required ====================

@pytest.mark.parametrize(
    "status_code,body,expected",
    [
        (400, '{"error":"invalid_grant"}', True),
        (400, '{"error":"invalid_client"}', True),
        (400, '{"error":"unauthorized_client"}', True),
        (400, '{"error":"unsupported_grant_type"}', False),
        (500, '{"error":"invalid_grant"}', False),
        (400, "not json", False),
    ],
)
def test_is_reauth_required(status_code, body, expected):
    exc = TibberTokenEndpointError(status_code, body)
    assert exc.is_reauth_required is expected


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
        with pytest.raises(TibberReauthRequiredError):
            client1._refresh()

    mock_post.assert_not_called()
    assert client1.tokens is None


def test_refresh_clears_store_on_invalid_grant(tmp_path):
    path = tmp_path / "tokens.json"
    store = TokenStore(path)
    store.save(_token(expired=True))
    client = _make_client(store)

    with patch("weconnect_mcp.adapter.tibber_client.httpx.post") as mock_post:
        mock_post.return_value = _fake_response(400, {"error": "invalid_grant"})
        with pytest.raises(TibberReauthRequiredError):
            client._refresh()

    assert client.tokens is None
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

    assert exc_info.value.is_reauth_required is False
    # Store untouched -- worth retrying later against the same refresh token.
    reloaded = TokenStore(path).load()
    assert reloaded is not None
    assert reloaded.refresh_token == stale.refresh_token


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

    # The plain "no refresh_token, can't interactively log in" error, not
    # the reauth-required subclass (that one means Tibber itself rejected
    # a token; this one means we never had one to try).
    assert not isinstance(exc_info.value, TibberReauthRequiredError)
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
    and raise TibberReauthRequiredError without a second network call.
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
        except TibberReauthRequiredError:
            outcomes[name] = "reauth_required"
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
