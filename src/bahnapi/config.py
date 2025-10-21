from __future__ import annotations

import os
from dataclasses import dataclass, replace
from typing import Optional

DEFAULT_TIMEOUT = 10


@dataclass
class Settings:
    client_id: Optional[str] = None
    api_key: Optional[str] = None
    timeout: int = DEFAULT_TIMEOUT


_active_settings = Settings(
    client_id=os.getenv("DB_CLIENT_ID"),
    api_key=os.getenv("DB_API_KEY"),
)


def configure(
    client_id: str,
    api_key: str,
    *,
    timeout: Optional[int] = None,
) -> None:
    """
    Configure global BahnAPI settings.

    Call this once in your application (e.g. during startup) if you prefer not to
    rely on environment variables.
    """
    global _active_settings
    _active_settings = Settings(
        client_id=client_id,
        api_key=api_key,
        timeout=timeout if timeout is not None else _active_settings.timeout,
    )


def get_settings() -> Settings:
    """Return a copy of the active settings."""
    return replace(_active_settings)
