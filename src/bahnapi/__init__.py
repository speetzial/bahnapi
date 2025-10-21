"""
Public API surface.
"""

from importlib import metadata

try:
    __version__ = metadata.version("bahnapi")
except metadata.PackageNotFoundError:  # pragma: no cover - during local dev
    __version__ = "0.0.0"

from .config import configure
from .departures import get_departures
from .stations import search_stations

__all__ = ["__version__", "configure", "get_departures", "search_stations"]
