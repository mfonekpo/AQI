"""Helpers for working with West African Time (WAT) in log and alert output.

These utilities keep datetime formatting consistent when writing operational
messages that should be interpreted in the Lagos timezone.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

WAT = ZoneInfo("Africa/Lagos")

def to_wat(utc_dt: datetime) -> datetime:
    """Convert a UTC datetime to West African Time for display purposes.

    Args:
        utc_dt: A timezone-aware UTC timestamp.

    Returns:
        A datetime object converted to the ``Africa/Lagos`` timezone.
    """
    return utc_dt.astimezone(WAT)

def now_wat() -> datetime:
    """Return the current UTC time converted to West African Time.

    Returns:
        The current wall-clock time in ``Africa/Lagos``.
    """
    return datetime.now(timezone.utc).astimezone(WAT)

def format_wat(utc_dt: datetime) -> str:
    """Format a UTC datetime as a readable West African Time string.

    Args:
        utc_dt: A timezone-aware UTC timestamp to render.

    Returns:
        A human-readable string suitable for logs and alerts.
    """
    return to_wat(utc_dt).strftime("%Y-%m-%d %H:%M:%S %Z")