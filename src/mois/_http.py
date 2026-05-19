"""httpx 기반 HTTP transport와 공통 응답 처리."""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from .exceptions import MoisRequestError, MoisServerError

DEFAULT_USER_AGENT = "python-mois-api/0.1 (+https://github.com/digitie/python-mois-api)"
RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
HTTP_CLIENT_ERROR = httpx.HTTPError


class SyncTransport(Protocol):
    """동기 클라이언트가 사용하는 최소 HTTP transport 프로토콜."""

    def get(self, url: str, **kwargs: Any) -> Any: ...

    def close(self) -> None: ...


class AsyncTransport(Protocol):
    """비동기 클라이언트가 사용하는 최소 HTTP transport 프로토콜."""

    async def get(self, url: str, **kwargs: Any) -> Any: ...

    async def aclose(self) -> None: ...


@dataclass(slots=True)
class SyncTokenBucket:
    """동기 호출용 token bucket rate limiter."""

    max_rps: float = 5.0
    capacity: float | None = None
    _tokens: float = field(init=False)
    _updated_at: float = field(init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self) -> None:
        if self.max_rps <= 0:
            raise ValueError("max_rps must be greater than 0")
        self.capacity = self.capacity or self.max_rps
        self._tokens = self.capacity
        self._updated_at = time.monotonic()

    def acquire(self) -> None:
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                wait_for = (1 - self._tokens) / self.max_rps
            time.sleep(wait_for)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._updated_at
        self._updated_at = now
        assert self.capacity is not None
        self._tokens = min(self.capacity, self._tokens + elapsed * self.max_rps)


@dataclass(slots=True)
class AsyncTokenBucket:
    """asyncio 호출용 token bucket rate limiter."""

    max_rps: float = 5.0
    capacity: float | None = None
    _tokens: float = field(init=False)
    _updated_at: float = field(init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        if self.max_rps <= 0:
            raise ValueError("max_rps must be greater than 0")
        self.capacity = self.capacity or self.max_rps
        self._tokens = self.capacity
        self._updated_at = time.monotonic()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                wait_for = (1 - self._tokens) / self.max_rps
            await asyncio.sleep(wait_for)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._updated_at
        self._updated_at = now
        assert self.capacity is not None
        self._tokens = min(self.capacity, self._tokens + elapsed * self.max_rps)


class SyncHttpxTransport:
    """httpx.Client 기반 동기 transport."""

    def __init__(
        self,
        *,
        timeout: float = 10.0,
        retries: int = 2,
        max_rps: float = 5.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.timeout = timeout
        self.retries = max(0, retries)
        self._bucket = SyncTokenBucket(max_rps=max_rps)
        self._client = client or httpx.Client(
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=timeout,
            follow_redirects=True,
        )
        self._owns_client = client is None

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        stream = bool(kwargs.pop("stream", False))
        timeout = kwargs.pop("timeout", self.timeout)
        attempts = self.retries + 1
        last_error: httpx.HTTPError | None = None
        for attempt in range(attempts):
            self._bucket.acquire()
            try:
                response = self._send_get(url, stream=stream, timeout=timeout, **kwargs)
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    raise
                time.sleep(_retry_delay(attempt))
                continue
            if response.status_code in RETRY_STATUS_CODES and attempt + 1 < attempts:
                response.close()
                time.sleep(_retry_delay(attempt))
                continue
            return response
        assert last_error is not None
        raise last_error

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _send_get(
        self,
        url: str,
        *,
        stream: bool,
        timeout: float,
        **kwargs: Any,
    ) -> httpx.Response:
        if not stream:
            return self._client.get(url, timeout=timeout, **kwargs)
        request = self._client.build_request("GET", url, timeout=timeout, **kwargs)
        return self._client.send(request, stream=True, follow_redirects=True)


class AsyncHttpxTransport:
    """httpx.AsyncClient 기반 asyncio transport."""

    def __init__(
        self,
        *,
        timeout: float = 10.0,
        retries: int = 2,
        max_rps: float = 5.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.timeout = timeout
        self.retries = max(0, retries)
        self._bucket = AsyncTokenBucket(max_rps=max_rps)
        self._client = client or httpx.AsyncClient(
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=timeout,
            follow_redirects=True,
        )
        self._owns_client = client is None

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        stream = bool(kwargs.pop("stream", False))
        timeout = kwargs.pop("timeout", self.timeout)
        attempts = self.retries + 1
        last_error: httpx.HTTPError | None = None
        for attempt in range(attempts):
            await self._bucket.acquire()
            try:
                response = await self._send_get(url, stream=stream, timeout=timeout, **kwargs)
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    raise
                await asyncio.sleep(_retry_delay(attempt))
                continue
            if response.status_code in RETRY_STATUS_CODES and attempt + 1 < attempts:
                await response.aclose()
                await asyncio.sleep(_retry_delay(attempt))
                continue
            return response
        assert last_error is not None
        raise last_error

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _send_get(
        self,
        url: str,
        *,
        stream: bool,
        timeout: float,
        **kwargs: Any,
    ) -> httpx.Response:
        if not stream:
            return await self._client.get(url, timeout=timeout, **kwargs)
        request = self._client.build_request("GET", url, timeout=timeout, **kwargs)
        return await self._client.send(request, stream=True, follow_redirects=True)


def build_session(
    retries: int = 2,
    *,
    timeout: float = 10.0,
    max_rps: float = 5.0,
) -> SyncHttpxTransport:
    """httpx 기반 동기 transport를 만듭니다."""

    return SyncHttpxTransport(timeout=timeout, retries=retries, max_rps=max_rps)


def build_async_session(
    retries: int = 2,
    *,
    timeout: float = 10.0,
    max_rps: float = 5.0,
) -> AsyncHttpxTransport:
    """httpx 기반 asyncio transport를 만듭니다."""

    return AsyncHttpxTransport(timeout=timeout, retries=retries, max_rps=max_rps)


def raise_for_http_error(response: Any, context: str) -> None:
    """HTTP 상태코드를 mois 예외로 매핑합니다."""

    status = getattr(response, "status_code", None)
    if status is None or 200 <= int(status) < 400:
        return
    if int(status) >= 500:
        raise MoisServerError(f"{context}: HTTP {status}")
    raise MoisRequestError(f"{context}: HTTP {status}")


def _retry_delay(attempt: int) -> float:
    return float(min(8.0, 0.5 * (2**attempt)))
