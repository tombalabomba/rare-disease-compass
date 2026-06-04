"""Tests für den zentralen HTTP-Client.

Alle Requests laufen über ``httpx.MockTransport`` — **kein** echter Netzwerk-
Call. Rate-Limit und Retry-Backoff nutzen gemockte ``sleep``/``monotonic``-
Funktionen, also **kein** echtes Warten.
"""

from __future__ import annotations

import httpx

from rdc.http_client import HttpClient


def _client(handler, **kwargs) -> HttpClient:
    kwargs.setdefault("min_interval", 0)
    return HttpClient(transport=httpx.MockTransport(handler), **kwargs)


def test_cache_hit_skips_transport() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    first = client.get("https://example.test/api", params={"q": "x"})
    second = client.get("https://example.test/api", params={"q": "x"})

    assert calls["n"] == 1  # zweiter Aufruf kommt aus dem Cache
    assert client.cache_hits == 1
    assert first.status_code == 200
    assert second.status_code == 200


def test_different_params_are_separate_cache_entries() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={})

    client = _client(handler)
    client.get("https://example.test/api", params={"q": "a"})
    client.get("https://example.test/api", params={"q": "b"})

    assert calls["n"] == 2
    assert client.cache_hits == 0


def test_retry_on_5xx_then_success() -> None:
    sequence = [500, 503, 200]
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        code = sequence[calls["n"]]
        calls["n"] += 1
        return httpx.Response(code, json={})

    slept: list[float] = []
    client = HttpClient(
        transport=httpx.MockTransport(handler),
        min_interval=0,
        sleep=slept.append,
    )

    response = client.get("https://example.test/x")

    assert response.status_code == 200
    assert calls["n"] == 3  # zwei Retries, dann Erfolg
    assert len(slept) == 2  # einmal Backoff je Retry


def test_retry_on_connection_error_then_success() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("boom", request=request)
        return httpx.Response(200, json={})

    slept: list[float] = []
    client = HttpClient(
        transport=httpx.MockTransport(handler),
        min_interval=0,
        sleep=slept.append,
    )

    response = client.get("https://example.test/x")

    assert response.status_code == 200
    assert calls["n"] == 2
    assert len(slept) == 1


def test_user_agent_header_set() -> None:
    seen: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["ua"] = request.headers.get("user-agent")
        return httpx.Response(200)

    client = _client(handler, user_agent="RDC-test/1.0")
    client.get("https://example.test/")

    assert seen["ua"] == "RDC-test/1.0"


def test_rate_limit_waits_min_interval() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    slept: list[float] = []
    clock = {"now": 0.0}
    client = HttpClient(
        transport=httpx.MockTransport(handler),
        min_interval=1.0,
        sleep=slept.append,
        monotonic=lambda: clock["now"],
    )

    # use_cache=False erzwingt zwei echte (gemockte) Requests an denselben Host.
    client.get("https://example.test/a", use_cache=False)
    client.get("https://example.test/a", use_cache=False)

    assert len(slept) == 1
    assert abs(slept[0] - 1.0) < 1e-9


def test_first_request_does_not_wait() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    slept: list[float] = []
    client = HttpClient(
        transport=httpx.MockTransport(handler),
        min_interval=1.0,
        sleep=slept.append,
        monotonic=lambda: 0.0,
    )

    client.get("https://example.test/a")

    assert slept == []
