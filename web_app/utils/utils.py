"""General-purpose utility functions."""
import time
from datetime import datetime as dt
from datetime import timezone as tz

# --------------------------------------------------------------------------------------
# Time-Related Functions


def get_now() -> str:
    """Get epoch time as a str."""
    return str(time.time())


def get_human_time(timestamp: str) -> str:
    """Get the given date and time with timezone, human-readable."""
    try:
        datetime = dt.fromtimestamp(float(timestamp))
    except ValueError:
        return timestamp

    timezone = dt.now(tz.utc).astimezone().tzinfo

    return f"{datetime.strftime('%Y-%m-%d %H:%M:%S')} {timezone}"


def get_human_now() -> str:
    """Get the current date and time with timezone, human-readable."""
    return get_human_time(get_now())
