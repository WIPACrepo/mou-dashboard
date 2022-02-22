"""General-purpose utility functions."""


import time
from datetime import datetime as dt
from typing import cast

from dateutil import parser as dp  # type: ignore[import]

# --------------------------------------------------------------------------------------
# Time-Related Functions


def iso_to_epoch(iso: str) -> str:
    """From ISO datetime, return the epoch timestamp."""
    return cast(str, dp.parse(iso).strftime("%s"))


def get_now() -> str:
    """Get epoch time as a str."""
    return str(time.time())


def get_iso(timestamp: str) -> str:
    """Get the ISO datetime, YYYY-MM-DD HH:MM:SS."""
    datetime = dt.fromtimestamp(float(timestamp))

    return datetime.strftime("%Y-%m-%d %H:%M:%S")


def get_human_time(timestamp: str, short: bool = False) -> str:
    """Get the given date and time with timezone, human-readable."""
    try:
        datetime = dt.fromtimestamp(float(timestamp))
    except ValueError:
        return timestamp

    if short:
        return datetime.strftime("%d-%b %Y")

    date = datetime.strftime("%d-%B %Y")
    time_ = datetime.strftime("%I:%M:%S%p").lower()
    timezone = datetime.astimezone().tzinfo
    return f"{date} ({time_} {timezone})"


def get_human_now(short: bool = False) -> str:
    """Get the current date and time with timezone, human-readable."""
    return get_human_time(get_now(), short)


def get_epoch_mins(mins: int) -> int:
    """Return the epoch timestamp int-divided by `60*mins`."""
    return int(time.time() / (60 * mins))
