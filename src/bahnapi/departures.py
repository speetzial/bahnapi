from __future__ import annotations

import datetime as dt
from typing import Dict, Iterable, List, Optional, Tuple

from .client import DBApiClient, create_default_client
from .parsers import parse_changes, parse_plan
from .utils import parse_time, to_jsonable


def get_departures(
    station_id: str,
    start_time: dt.datetime,
    end_time: dt.datetime,
    *,
    client: Optional[DBApiClient] = None,
    include_recent_changes: bool = False,
) -> List[Dict]:
    """
    Fetch departures for a station in the given timeframe (inclusive).

    Args:
        station_id: EVA number as string.
        start_time: Beginning of interval (datetime).
        end_time: End of interval (datetime).
        client: Optional DBApiClient (auto-created if omitted).
        include_recent_changes: Additionally merge `/rchg` delta on top of full changes.

    Returns:
        List of dictionaries sorted by effective departure time.
    """
    if not station_id:
        raise ValueError("station_id is required.")
    if start_time > end_time:
        raise ValueError("start_time must not be after end_time.")

    start_time = _normalize_datetime(start_time)
    end_time = _normalize_datetime(end_time)

    api_client = client or create_default_client()

    try:
        plan_entries = _collect_plan_entries(api_client, station_id, start_time, end_time)
        changes = _collect_changes(api_client, station_id, include_recent_changes)
        departures = _merge_plan_and_changes(plan_entries, changes)
    finally:
        if client is None:
            api_client.close()

    filtered = _filter_by_interval(departures, start_time, end_time)
    filtered.sort(
        key=lambda item: parse_time(item["departure_actual"])
        or parse_time(item["departure_planned"])
    )
    return filtered


# --------------------------------------------------------------------------- #
# Internal helpers


def _collect_plan_entries(
    client: DBApiClient,
    station_id: str,
    start_time: dt.datetime,
    end_time: dt.datetime,
) -> Dict[str, Dict]:
    """Fetch and parse plan slices covering the timeframe."""
    plan_events: Dict[str, Dict] = {}
    for date_str, hour_str in _iter_time_slices(start_time, end_time):
        xml_payload = client.fetch_plan(station_id, date_str, hour_str)
        plan_chunk = parse_plan(xml_payload)
        plan_events.update(plan_chunk)
    return plan_events


def _collect_changes(
    client: DBApiClient,
    station_id: str,
    include_recent: bool,
) -> Dict[str, Dict]:
    """Fetch full (and optionally recent) changes."""
    combined: Dict[str, Dict] = {}
    xml_full = client.fetch_full_changes(station_id)
    combined.update(parse_changes(xml_full))

    if include_recent:
        xml_recent = client.fetch_recent_changes(station_id)
        combined.update(parse_changes(xml_recent))

    return combined


def _merge_plan_and_changes(
    plan_events: Dict[str, Dict],
    changes: Dict[str, Dict],
) -> List[Dict]:
    merged: List[Dict] = []

    all_ids = set(plan_events.keys()) | set(changes.keys())

    for stop_id in all_ids:
        plan = plan_events.get(stop_id, {})
        change = changes.get(stop_id, {})

        line_info = plan.get("planned_line") or {}

        planned_departure = plan.get("planned_departure")
        actual_departure = change.get("actual_departure") or planned_departure

        delay_minutes = None
        if actual_departure and planned_departure:
            delta = actual_departure - planned_departure
            delay_minutes = int(delta.total_seconds() // 60)

        messages = _merge_messages(
            plan.get("remarks", []),
            change.get("messages", []),
            change.get("station_messages", []),
        )

        result = {
            "stop_id": stop_id,
            "station_eva": change.get("station_eva") or plan.get("station_eva"),
            "departure_planned": to_jsonable(planned_departure),
            "departure_actual": to_jsonable(actual_departure),
            "delay_minutes": delay_minutes,
            "platform_planned": plan.get("planned_platform"),
            "platform_actual": change.get("actual_platform")
            or plan.get("planned_platform"),
            "status": change.get("status"),
            "destination_name": change.get("destination")
            or plan.get("planned_destination"),
            "train_category": line_info.get("category"),
            "train_number": line_info.get("number"),
            "operator": line_info.get("operator"),
        }
        if messages:
            result["messages"] = messages

        merged.append(result)

    return merged


def _filter_by_interval(
    departures: List[Dict],
    start_time: dt.datetime,
    end_time: dt.datetime,
) -> List[Dict]:
    filtered: List[Dict] = []
    for dep in departures:
        actual = parse_time(dep.get("departure_actual"))
        planned = parse_time(dep.get("departure_planned"))
        pivot = actual or planned
        if pivot is None:
            continue
        if start_time <= pivot <= end_time:
            filtered.append(dep)
    return filtered


def _merge_messages(*message_groups: Iterable[Dict]) -> List[Dict]:
    merged: List[Dict] = []
    seen_ids = set()
    for group in message_groups:
        if not group:
            continue
        for message in group:
            message_id = message.get("id")
            if message_id and message_id in seen_ids:
                continue
            if message_id:
                seen_ids.add(message_id)
            simplified = {
                "id": message.get("id"),
                "type": message.get("type"),
                "code": message.get("code"),
                "category": message.get("category"),
                "priority": message.get("priority"),
                "text": message.get("text"),
                "valid_from": message.get("valid_from"),
                "valid_to": message.get("valid_to"),
            }
            merged.append(simplified)
    return merged


def _iter_time_slices(
    start_time: dt.datetime,
    end_time: dt.datetime,
) -> Iterable[Tuple[str, str]]:
    """Yield (date, hour) slices covering the [start, end] range."""
    # normalise to minute precision
    start = start_time.replace(minute=0, second=0, microsecond=0)
    end = end_time.replace(minute=0, second=0, microsecond=0)

    current = start
    while current <= end:
        yield current.strftime("%y%m%d"), current.strftime("%H")
        current += dt.timedelta(hours=1)


# Allow module-level convenience factory --------------------------------------

__all__ = ["get_departures"]


def _normalize_datetime(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(dt.timezone.utc).replace(tzinfo=None)
