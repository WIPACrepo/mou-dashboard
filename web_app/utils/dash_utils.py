"""Utility module for front-end Dash functions."""


from typing import cast

import dash  # type: ignore[import]

from .types import Record, Table

# Constants
_OC_SUFFIX = "_original"


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


def add_original_copies_to_record(record: Record) -> Record:
    """Make a copy of each field to detect changed values."""
    for field in record:  # don't add copies of copies, AKA make it safe to call this 2x
        if field.endswith(_OC_SUFFIX):
            return record

    record.update({f"{i}{_OC_SUFFIX}": v for i, v in record.items()})
    return record


def add_original_copies(table: Table) -> Table:
    """Make a copy of each column to detect changed values.

    Hide these duplicate columns by not adding them to the 'columns'
    property.
    """
    for record in table:
        add_original_copies_to_record(record)

    return table


def _without_original_copies_from_record(record: Record) -> Record:
    return {k: v for k, v in record.items() if not k.endswith(_OC_SUFFIX)}


def without_original_copies(table: Table) -> Table:
    """Copy but leave out the original copies used to detect changed values."""
    new_table = []

    if table:
        for record in table:
            new_table.append(_without_original_copies_from_record(record))

    return new_table


def get_changed_data_filter_query(column: str) -> str:
    """Return the filter query for detecting changed data.

    For use as an "if" value in a DataTable.style_data_conditional
    entry.
    """
    return f"{{{column}}} != {{{column}{_OC_SUFFIX}}}"
