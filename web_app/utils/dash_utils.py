"""Utility module for front-end Dash functions."""


import time
from typing import cast, Final

import dash  # type: ignore[import]

from .types import Record, Table

# Constants
_OC_SUFFIX: Final[str] = "_original"
_RECENT_THRESHOLD: Final[float] = 1.0


# --------------------------------------------------------------------------------------
# Function(s) that really should be in a dash library


def triggered_id() -> str:
    """Return the id of the property that triggered the callback.

    https://dash.plotly.com/advanced-callbacks
    """
    trig = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    return cast(str, trig)


# --------------------------------------------------------------------------------------
# Data Functions


def add_original_copies_to_record(record: Record, novel: bool = False) -> Record:
    """Make a copy of each field in an new column to detect changed values.

    These columns aren't meant to be seen by the user.

    Arguments:
        record {Record} -- the record, that will be updated

    Keyword Arguments:
        novel {bool} -- if True, don't copy values, just set as '' (default: {False})

    Returns:
        Record -- the argument value
    """
    for field in record:  # don't add copies of copies, AKA make it safe to call this 2x
        if field.endswith(_OC_SUFFIX):
            return record

    if not novel:
        record.update({f"{k}{_OC_SUFFIX}": v for k, v in record.items()})
    else:
        record.update({f"{k}{_OC_SUFFIX}": "" for k, _ in record.items()})

    return record


def add_original_copies(table: Table) -> Table:
    """Make a copy of each column to detect changed values.

    Hide these duplicate columns by not adding them to the 'columns'
    property.
    """
    for record in table:
        add_original_copies_to_record(record)

    return table


def without_original_copies_from_record(record: Record) -> Record:
    """Copy but leave out the original copies used to detect changed values."""
    return {k: v for k, v in record.items() if not k.endswith(_OC_SUFFIX)}


def get_changed_data_filter_query(column: str) -> str:
    """Return the filter query for detecting changed data.

    For use as an "if" value in a DataTable.style_data_conditional
    entry.
    """
    return f"{{{column}}} != {{{column}{_OC_SUFFIX}}}"


def get_now() -> str:
    """Get epoch time as a str."""
    return str(time.time())


def was_recent(timestamp: str) -> bool:
    """Return whether the event last occurred w/in the `_FILTER_THRESHOLD`."""
    if not timestamp:
        return False

    diff = float(get_now()) - float(timestamp)

    if diff < _RECENT_THRESHOLD:
        print(f"RECENT EVENT ({diff})")
        return True

    print(f" not recent event ({diff})")
    return False
