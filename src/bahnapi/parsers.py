from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

from .utils import parse_time


def parse_station_list(xml_text: str) -> List[Dict[str, str]]:
    """Parse XML response of /station endpoint."""
    if not xml_text:
        return []
    root = ET.fromstring(xml_text)
    stations = []
    for station in root.findall(".//station"):
        stations.append(
            {
                "name": station.attrib.get("name"),
                "eva": station.attrib.get("eva"),
                "ds100": station.attrib.get("ds100"),
                "meta": station.attrib.get("meta"),
                "platform": station.attrib.get("p"),
                "raw": station.attrib,
            }
        )
    return stations


def parse_plan(xml_text: str) -> Dict[str, Dict]:
    """Parse /plan response into a mapping keyed by stop id."""
    if not xml_text:
        return {}

    root = ET.fromstring(xml_text)
    plan_events: Dict[str, Dict] = {}

    for station in root.findall("s"):
        stop_id = station.attrib.get("id")
        if not stop_id:
            continue

        dp = station.find("dp")
        if dp is None:
            # skip stops without departure component
            continue

        path = _split_path(dp.attrib.get("ppth"))
        line_info = _extract_line_info(station.find("tl"))

        plan_events[stop_id] = {
            "stop_id": stop_id,
            "station_eva": station.attrib.get("eva"),
            "planned_departure": parse_time(dp.attrib.get("pt")),
            "planned_platform": dp.attrib.get("pp"),
            "planned_path": path,
            "planned_destination": path[-1] if path else None,
            "planned_line": line_info,
            "remarks": _extract_messages(station.findall("m")),
            "raw": {
                "station": station.attrib,
                "departure": dp.attrib,
            },
        }

    return plan_events


def parse_changes(xml_text: str) -> Dict[str, Dict]:
    """Parse /fchg or /rchg response into mapping keyed by stop id."""
    if not xml_text:
        return {}

    root = ET.fromstring(xml_text)
    change_events: Dict[str, Dict] = {}

    for station in root.findall("s"):
        stop_id = station.attrib.get("id")
        if not stop_id:
            continue

        dp = station.find("dp")
        if dp is None:
            continue

        path = _split_path(dp.attrib.get("ppth"))

        change_events[stop_id] = {
            "stop_id": stop_id,
            "station_eva": station.attrib.get("eva"),
            "actual_departure": parse_time(dp.attrib.get("ct") or dp.attrib.get("rt")),
            "actual_platform": dp.attrib.get("cp"),
            "status": dp.attrib.get("cs"),
            "messages": _extract_messages(dp.findall("m")),
            "path": path,
            "destination": path[-1] if path else None,
            "raw": {
                "station": station.attrib,
                "departure": dp.attrib,
            },
        }

        # propagate station-level messages if present
        station_messages = _extract_messages(station.findall("m"))
        if station_messages:
            change_events[stop_id]["station_messages"] = station_messages

    return change_events


def _split_path(path: Optional[str]) -> List[str]:
    if not path:
        return []
    return [segment.strip() for segment in path.split("|") if segment.strip()]


def _extract_line_info(line_element: Optional[ET.Element]) -> Optional[Dict[str, Optional[str]]]:
    if line_element is None:
        return None
    attrs = line_element.attrib
    return {
        "category": attrs.get("c"),
        "number": attrs.get("n"),
        "type": attrs.get("t"),
        "operator": attrs.get("o"),
        "line": attrs.get("l"),
        "additional": attrs,
    }


def _extract_messages(elements: List[ET.Element]) -> List[Dict[str, Optional[str]]]:
    messages: List[Dict[str, Optional[str]]] = []
    for msg in elements:
        attrs = msg.attrib
        messages.append(
            {
                "id": attrs.get("id"),
                "type": attrs.get("t"),
                "code": attrs.get("c"),
                "category": attrs.get("cat"),
                "priority": attrs.get("pr"),
                "timestamp": attrs.get("ts"),
                "valid_from": attrs.get("from"),
                "valid_to": attrs.get("to"),
                "text": msg.text,
                "raw": attrs,
            }
        )
    return messages
