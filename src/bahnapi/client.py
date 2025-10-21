from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional

import requests

from .config import DEFAULT_TIMEOUT, get_settings
from .exceptions import AuthenticationError, BahnAPIError, RateLimitError

BASE_URL = "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1"
PLAN_CACHE_TTL = 60 * 60  # 1 hour
CHANGES_CACHE_TTL = 30  # seconds
STATION_CACHE_TTL = 12 * 60 * 60  # 12 hours


@dataclass
class _CacheEntry:
    expires_at: float
    value: str


class DBApiClient:
    """Lightweight client for the Deutsche Bahn Timetables API."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        api_key: Optional[str] = None,
        *,
        timeout: int = DEFAULT_TIMEOUT,
        session_factory: Callable[[], requests.Session] = requests.Session,
    ) -> None:
        settings = get_settings()

        self.client_id = client_id or settings.client_id or os.getenv("DB_CLIENT_ID")
        self.api_key = api_key or settings.api_key or os.getenv("DB_API_KEY")

        if not self.client_id or not self.api_key:
            raise AuthenticationError(
                "DB Client ID and API Key must be provided via arguments or environment variables "
                "(DB_CLIENT_ID / DB_API_KEY)."
            )

        self._timeout = timeout if timeout != DEFAULT_TIMEOUT else settings.timeout
        self._session = session_factory()
        self._session.headers.update(
            {
                "DB-Client-Id": self.client_id,
                "DB-Api-Key": self.api_key,
                "Accept": "application/xml",
                "User-Agent": "bahnapi/0.1.0",
            }
        )
        self._cache: Dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()

    def close(self) -> None:
        self._session.close()

    # Public endpoints --------------------------------------------------
    def fetch_plan(self, eva_number: str, date: str, hour: str) -> str:
        path = f"/plan/{eva_number}/{date}/{hour}"
        return self._cached_get(path, PLAN_CACHE_TTL)

    def fetch_full_changes(self, eva_number: str) -> str:
        path = f"/fchg/{eva_number}"
        return self._cached_get(path, CHANGES_CACHE_TTL)

    def fetch_recent_changes(self, eva_number: str) -> str:
        path = f"/rchg/{eva_number}"
        return self._cached_get(path, CHANGES_CACHE_TTL)

    def fetch_station(self, pattern: str) -> str:
        path = f"/station/{pattern}"
        return self._cached_get(path, STATION_CACHE_TTL)

    # Internal helpers --------------------------------------------------
    def _cached_get(self, path: str, ttl: int) -> str:
        cache_key = path
        now = time.time()
        with self._lock:
            entry = self._cache.get(cache_key)
            if entry and entry.expires_at > now:
                return entry.value

        payload = self._request("GET", path)

        with self._lock:
            self._cache[cache_key] = _CacheEntry(expires_at=now + ttl, value=payload)
        return payload

    def _request(self, method: str, path: str) -> str:
        url = f"{BASE_URL}{path}"
        response = self._session.request(method, url, timeout=self._timeout)

        if response.status_code in {401, 403}:
            raise AuthenticationError("Authentication failed against the DB API.")
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded when calling the DB API.")
        if 400 <= response.status_code < 600:
            raise BahnAPIError(
                f"DB API error: {response.status_code} - {response.text[:200]}"
            )

        return response.text


def create_default_client() -> DBApiClient:
    """Factory that reads credentials from environment variables."""
    settings = get_settings()
    return DBApiClient(
        client_id=settings.client_id,
        api_key=settings.api_key,
        timeout=settings.timeout,
    )
