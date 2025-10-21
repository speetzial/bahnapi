from __future__ import annotations

import datetime as dt
from typing import Optional


def parse_time(value: Optional[str]) -> Optional[dt.datetime]:
    """
    Parse DB API timestamp attributes (ISO 8601 or YYMMDDHHMM format).

    Returns naive datetime in local timezone assumptions. If format is unknown,
    returns None.
    """
    if not value:
        return None
    # Most attributes are ISO 8601.
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        pass
    # Fallback: YYMMDDHHmm or similar numeric string.
    if len(value) in (10, 12):
        try:
            if len(value) == 10:
                return dt.datetime.strptime(value, "%y%m%d%H%M")
            return dt.datetime.strptime(value, "%Y%m%d%H%M")
        except ValueError:
            return None
    return None


def to_jsonable(dt_value: Optional[dt.datetime]) -> Optional[str]:
    """Convert datetime to ISO string; returns None if input missing."""
    if dt_value is None:
        return None
    if dt_value.tzinfo:
        return dt_value.isoformat()
    return dt_value.isoformat()
