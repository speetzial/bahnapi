from __future__ import annotations

from typing import List, Optional

from .client import DBApiClient, create_default_client
from .exceptions import StationLookupError
from .parsers import parse_station_list


def search_stations(
    pattern: str,
    *,
    client: Optional[DBApiClient] = None,
    limit: Optional[int] = None,
) -> List[dict]:
    """
    Search for stations by name prefix, EVA number, or DS100 code.

    Returns a list of dicts with station metadata.
    """
    if not pattern:
        raise StationLookupError("Station search pattern must not be empty.")

    api_client = client or create_default_client()
    xml_payload = api_client.fetch_station(pattern)
    stations = parse_station_list(xml_payload)

    if limit is not None:
        stations = stations[:limit]

    if client is None:
        api_client.close()

    return stations


def resolve_station_eva(
    pattern: str,
    *,
    client: Optional[DBApiClient] = None,
) -> str:
    """
    Resolve a single EVA number from a pattern.

    Raises StationLookupError if result is empty or ambiguous.
    """
    matches = search_stations(pattern, client=client)
    if not matches:
        raise StationLookupError(f"No station found for pattern '{pattern}'.")
    if len(matches) > 1:
        names = ", ".join(station["name"] for station in matches[:5])
        raise StationLookupError(
            f"Pattern '{pattern}' is ambiguous ({len(matches)} matches): {names}"
        )
    eva = matches[0].get("eva")
    if not eva:
        raise StationLookupError(f"Station '{matches[0]}' has no EVA number.")
    return eva
