from datetime import datetime, timezone
from zoneinfo import ZoneInfo

WAT = ZoneInfo("Africa/Lagos")

def to_wat(utc_dt: datetime) -> datetime:
    """Convert a UTC datetime to WAT for display purposes only."""
    return utc_dt.astimezone(WAT)

def now_wat() -> datetime:
    """Current time in WAT — for logging and display only."""
    return datetime.now(timezone.utc).astimezone(WAT)

def format_wat(utc_dt: datetime) -> str:
    """Format a UTC datetime as a readable WAT string."""
    return to_wat(utc_dt).strftime("%Y-%m-%d %H:%M:%S %Z")