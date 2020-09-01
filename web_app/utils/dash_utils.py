"""Utility module for front-end Dash functions."""


from typing import cast, Collection, Dict, List, Union

import dash  # type: ignore[import]

# --------------------------------------------------------------------------------------
# Types


DataEntry = Union[int, float, str]  # just data
_StrDict = Dict[str, str]  # Ceci n'est pas une pipe


# DataTable properties
TData = List[Dict[str, DataEntry]]  # data
SDCond = List[Dict[str, Collection[str]]]  # style_data_conditional
DDown = Dict[str, Dict[str, List[_StrDict]]]  # dropdown
DDCond = List[Dict[str, Union[_StrDict, List[_StrDict]]]]  # dropdown_conditional


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


def create_hidden_duplicate_columns(
    table: List[Dict[str, DataEntry]]
) -> List[Dict[str, DataEntry]]:
    """Make a hidden copy of each column to detect changed values.

    They're "hidden" b/c these duplicate columns aren't in the 'columns'
    property.
    """
    for record in table:
        record.update({f"{i}_hidden": v for i, v in record.items()})

    return table


def remove_hidden_duplicate_column_entries(
    record: Dict[str, DataEntry]
) -> Dict[str, DataEntry]:
    """Remove the hidden copies used to detect changed values, in a row."""
    return {k: v for k, v in record.items() if not k.endswith("_hidden")}


def _has_field_changed(record: Dict[str, DataEntry], field_name: str) -> bool:
    try:
        return record[field_name] != record[f"{field_name}_hidden"]
    except KeyError:
        return False


def has_record_changed(record: Dict[str, DataEntry]) -> bool:
    """Return whether the record has been changed by the user."""
    for field_name in record:
        if _has_field_changed(record, field_name):
            return True
    return False
