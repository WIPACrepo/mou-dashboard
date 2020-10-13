"""Utility module for front-end Dash functions."""


import logging
import time
from datetime import datetime as dt
from datetime import timezone as tz
from typing import cast, Final

import dash  # type: ignore[import]

# Constants
_RECENT_THRESHOLD: Final[float] = 1.0


class Color:  # pylint: disable=R0903
    """Dash Colors."""

    PRIMARY = "primary"  # blue
    SECONDARY = "secondary"  # gray
    DARK = "dark"  # black
    SUCCESS = "success"  # green
    WARNING = "warning"  # yellow
    DANGER = "danger"  # red
    INFO = "info"  # teal
    LIGHT = "light"  # gray on white
    LINK = "link"  # blue on transparent


# --------------------------------------------------------------------------------------
# Function(s) that really should be in a dash library


def triggered_id() -> str:
    """Return the id of the property that triggered the callback.

    https://dash.plotly.com/advanced-callbacks
    """
    trig = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    return cast(str, trig)


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


def was_recent(timestamp: str) -> bool:
    """Return whether the event last occurred w/in the `_FILTER_THRESHOLD`."""
    if not timestamp:
        return False

    diff = float(get_now()) - float(timestamp)

    if diff < _RECENT_THRESHOLD:
        logging.debug(f"RECENT EVENT ({diff})")
        return True

    logging.debug(f"NOT RECENT EVENT ({diff})")
    return False
