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


def add_original_copies(table: Table) -> Table:
    """Make a copy of each column to detect changed values.

    Hide these duplicate columns by not adding them to the 'columns'
    property.
    """
    for record in table:
        record.update({f"{i}{_OC_SUFFIX}": v for i, v in record.items()})

    return table


def remove_original_copies(record: Record) -> Record:
    """Remove the original copies used to detect changed values in a record."""
    return {k: v for k, v in record.items() if not k.endswith(_OC_SUFFIX)}


def _has_field_changed(record: Record, field_name: str) -> bool:
    try:
        return record[field_name] != record[f"{field_name}{_OC_SUFFIX}"]
    except KeyError:
        return False


def has_record_changed(record: Record) -> bool:
    """Return whether the record has been changed by the user."""
    for field_name in record:
        if _has_field_changed(record, field_name):
            return True
    return False


def get_changed_data_filter_query(column: str) -> str:
    """Return the filter query for detecting changed data.

    For use as an "if" value in a DataTable.style_data_conditional
    entry.
    """
    return f"{{{column}}} != {{{column}{_OC_SUFFIX}}}"
