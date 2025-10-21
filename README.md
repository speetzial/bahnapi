## Installation

```bash
pip install bahnapi
```

Python 3.9 or newer is required. The only runtime dependency is `requests>=2.31.0`.

## Configuration

The Deutsche Bahn API requires credentials. Configure BahnAPI in one of two ways.

### Programmatic configuration

```python
import bahnapi

bahnapi.configure(
    client_id="YOUR_CLIENT_ID",
    api_key="YOUR_API_KEY",
    timeout=15,  # optional, seconds
)
```

## Quick Start

```python
import datetime as dt
import bahnapi

bahnapi.configure("YOUR_CLIENT_ID", "YOUR_API_KEY")

now = dt.datetime.now(dt.UTC)
departures = bahnapi.get_departures(
    station_id="8011160",  # Berlin Hbf
    start_time=now,
    end_time=now + dt.timedelta(hours=1),
    include_recent_changes=True,  # also merge /rchg
)

for dep in departures[:3]:
    print(
        dep["departure_planned"],
        dep["departure_actual"],
        dep["destination_name"],
        dep["delay_minutes"],
    )
```

Each entry is intentionally compact:

- `stop_id`, `station_eva`
- `departure_planned`, `departure_actual`, `delay_minutes`
- `platform_planned`, `platform_actual`
- `destination_name`, `train_category`, `train_number`, `operator`
- optional `messages` list (only essential fields)

## Station Search

```python
from bahnapi import search_stations

matches = search_stations("Berlin Hbf", limit=5)
if matches:
    print(matches[0]["eva"])
```

Use `bahnapi.stations.resolve_station_eva(pattern)` to enforce a single match; it raises `StationLookupError` when ambiguous or missing.

## API Overview

```python
bahnapi.configure(client_id, api_key, timeout=10)
bahnapi.get_departures(station_id, start_time, end_time, include_recent_changes=False)
bahnapi.search_stations(pattern, limit=None)
bahnapi.stations.resolve_station_eva(pattern)
```

Exceptions live in `bahnapi.exceptions`:

- `BahnAPIError` (base class)
- `AuthenticationError`
- `RateLimitError`
- `StationLookupError`

## License

Released under the MIT License (see `LICENSE`).

## Acknowledgements

This project is unaffiliated with Deutsche Bahn. It simply wraps the official Timetables API provided via the DB API Marketplace. Always consult the official documentation for rate limits and conditions.*** End Patch
