"""Zentraler HTTP-Zugriff für alle Quellen-Subkommandos.

Eine einzige Stelle kapselt User-Agent, Timeout, Retry mit Backoff, ein
höfliches Rate-Limit (Mindestabstand pro Host) und einen prozesslokalen
Cache. So erfindet keine Quelle (CLI-02…06) diese Mechanik neu.

Der Konstruktor akzeptiert einen injizierbaren ``transport`` sowie austausch-
bare ``sleep``/``monotonic``-Funktionen — Tests speisen ``httpx.MockTransport``
ein und mocken die Zeit, damit **kein** echter Netzwerk-Call und **kein**
echtes Warten passiert.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlencode

import httpx

from . import __version__

DEFAULT_USER_AGENT = (
    f"RareDiseaseCompass/{__version__} "
    "(+https://github.com/rare-disease-compass; research use; contact via repo)"
)
DEFAULT_TIMEOUT = 20.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 0.5
# ~3 Requests/s als höflicher Default für öffentliche Medizin-APIs.
DEFAULT_MIN_INTERVAL = 0.34


class HttpClient:
    """Konfigurierter ``httpx.Client`` mit Cache, Rate-Limit und Retry."""

    def __init__(
        self,
        *,
        base_url: str = "",
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        min_interval: float = DEFAULT_MIN_INTERVAL,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.base_url = base_url
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.min_interval = min_interval
        self._sleep = sleep
        self._monotonic = monotonic

        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            transport=transport,
            headers={"User-Agent": user_agent},
            follow_redirects=True,
        )

        self._cache: dict[str, httpx.Response] = {}
        self._last_request: dict[str, float] = {}
        self.cache_hits = 0

    # -- öffentliche API ---------------------------------------------------

    def get(
        self,
        url: str,
        params: Mapping[str, Any] | None = None,
        *,
        use_cache: bool = True,
    ) -> httpx.Response:
        return self.request("GET", url, params=params, use_cache=use_cache)

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        use_cache: bool = True,
    ) -> httpx.Response:
        key = self._cache_key(method, url, params)
        if use_cache and key in self._cache:
            self.cache_hits += 1
            return self._cache[key]

        response = self._request_with_retry(method, url, params)

        if use_cache:
            self._cache[key] = response
        return response

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- intern ------------------------------------------------------------

    def _request_with_retry(
        self,
        method: str,
        url: str,
        params: Mapping[str, Any] | None,
    ) -> httpx.Response:
        response: httpx.Response | None = None
        for attempt in range(self.max_retries + 1):
            self._respect_rate_limit(url)
            try:
                response = self._client.request(method, url, params=params)
            except httpx.TransportError:
                if attempt >= self.max_retries:
                    raise
                self._sleep(self._backoff(attempt))
                continue
            # 429 (Rate Limit) und 5xx sind transient → mit Backoff erneut
            # versuchen. 4xx (außer 429) sind endgültig und werden zurückgegeben,
            # damit die Quellen sie von "gefunden, aber leer" unterscheiden können.
            retryable = response.status_code == 429 or response.status_code >= 500
            if retryable and attempt < self.max_retries:
                self._sleep(self._backoff(attempt))
                continue
            return response
        # max_retries == 0 oder letzter Versuch lieferte weiterhin 5xx.
        assert response is not None
        return response

    def _backoff(self, attempt: int) -> float:
        return self.backoff_base * (2**attempt)

    def _respect_rate_limit(self, url: str) -> None:
        if self.min_interval <= 0:
            return
        host = self._host_of(url)
        now = self._monotonic()
        last = self._last_request.get(host)
        if last is not None:
            wait = self.min_interval - (now - last)
            if wait > 0:
                self._sleep(wait)
                now = self._monotonic()
        self._last_request[host] = now

    def _host_of(self, url: str) -> str:
        parsed = httpx.URL(url)
        if not parsed.host and self.base_url:
            parsed = httpx.URL(self.base_url)
        return parsed.host or ""

    def _cache_key(
        self,
        method: str,
        url: str,
        params: Mapping[str, Any] | None,
    ) -> str:
        encoded = urlencode(sorted((params or {}).items()))
        return f"{method.upper()} {url}?{encoded}"
