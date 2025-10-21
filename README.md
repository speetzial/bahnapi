# BahnAPI

BahnAPI is a lightweight Python wrapper around the Deutsche Bahn Timetables API. It merges planned timetable data with live updates and exposes a concise, Pythonic interface.

## Features

- `requests`-based HTTP client with simple in-memory caching.
- Unified departures API combining `/plan`, `/fchg`, and optional `/rchg` data.
- Station lookup utilities for EVA numbers, DS100 codes, and name prefixes.
- Declarative configuration via `bahnapi.configure(...)` or environment variables.
- Ships with a small CLI demo (`bahnapi-test`) to try things quickly.

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

### Environment variables

```bash
export DB_CLIENT_ID="YOUR_CLIENT_ID"
export DB_API_KEY="YOUR_API_KEY"
```

On Windows PowerShell:

```powershell
$env:DB_CLIENT_ID="YOUR_CLIENT_ID"
$env:DB_API_KEY="YOUR_API_KEY"
```

If neither option is used, any API call raises `bahnapi.exceptions.AuthenticationError`.

## Quick Start

```python
import datetime as dt
import bahnapi

bahnapi.configure("YOUR_CLIENT_ID", "YOUR_API_KEY")

now = dt.datetime.now(dt.timezone.utc)
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

## Command Line Demo

After installation, use the bundled helper:

```bash
bahnapi-test 8011160 --hours 1 --recent \
    --client-id YOUR_CLIENT_ID --api-key YOUR_API_KEY
```

Useful options:

- `--resolve` resolves a station pattern to an EVA number.
- `--search` prints station matches and exits.
- `--recent` merges `/rchg` responses for incremental updates.

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

## Development

```bash
git clone https://github.com/YOUR_ORG/bahnapi.git
cd bahnapi
python -m venv .venv
. .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -e .
```

Run `python test.py` to exercise the API with your credentials.

## License

Released under the MIT License (see `LICENSE`).

## Acknowledgements

This project is unaffiliated with Deutsche Bahn. It simply wraps the official Timetables API provided via the DB API Marketplace. Always consult the official documentation for rate limits and conditions.
