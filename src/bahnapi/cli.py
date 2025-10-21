from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from typing import Optional

from . import configure, get_departures, search_stations
from .stations import resolve_station_eva


def _configure_from_args(args: argparse.Namespace) -> None:
    if args.client_id or args.api_key:
        if not args.client_id or not args.api_key:
            raise SystemExit("Both --client-id and --api-key must be provided together.")
        configure(args.client_id, args.api_key)


def _positive_float(value: str) -> float:
    try:
        hours = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if hours <= 0:
        raise argparse.ArgumentTypeError("Value must be positive.")
    return hours


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bahnapi-test",
        description="Query Deutsche Bahn Timetables departures via the BahnAPI library.",
    )
    parser.add_argument(
        "station",
        help="EVA number or station pattern (combine with --resolve to auto-detect).",
    )
    parser.add_argument(
        "--hours",
        type=_positive_float,
        default=1.0,
        help="Time range in hours starting now (default: 1).",
    )
    parser.add_argument(
        "--client-id",
        help="DB API client id (overrides configuration/environment).",
    )
    parser.add_argument(
        "--api-key",
        help="DB API key (overrides configuration/environment).",
    )
    parser.add_argument(
        "--resolve",
        action="store_true",
        help="Resolve station pattern to EVA using the /station endpoint.",
    )
    parser.add_argument(
        "--recent",
        action="store_true",
        help="Merge recent changes (/rchg) in addition to full changes.",
    )
    parser.add_argument(
        "--search",
        action="store_true",
        help="Only perform station lookup and print matches.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of station matches to show with --search (default: 10).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON output instead of a human-readable summary.",
    )

    args = parser.parse_args(argv)

    _configure_from_args(args)

    if args.search:
        stations = search_stations(args.station, limit=args.limit)
        print(json.dumps(stations, indent=2, ensure_ascii=False))
        return 0

    station_id = args.station
    if args.resolve:
        station_id = resolve_station_eva(args.station)

    now = dt.datetime.now(dt.timezone.utc)
    end = now + dt.timedelta(hours=args.hours)

    departures = get_departures(
        station_id=station_id,
        start_time=now,
        end_time=end,
        include_recent_changes=args.recent,
    )

    if args.json:
        print(json.dumps(departures, indent=2, ensure_ascii=False))
        return 0

    if not departures:
        print("No departures found in the requested interval.")
        return 0

    for dep in departures:
        planned = dep.get("departure_planned") or "-"
        actual = dep.get("departure_actual") or "-"
        delay = dep.get("delay_minutes")
        destination = dep.get("destination_name") or "-"
        platform = dep.get("platform_actual") or dep.get("platform_planned") or "-"
        line = dep.get("train_category") or ""
        number = dep.get("train_number") or ""
        operator = dep.get("operator") or ""
        status = dep.get("status") or ""
        delay_str = f"{delay:+d} min" if delay is not None else ""
        label = " ".join(part for part in [line, number] if part)
        print(f"{planned} -> {actual} | {destination} | {label} | Pl.: {platform} | {delay_str} {status} {operator}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
