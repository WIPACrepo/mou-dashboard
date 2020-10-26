"""Utility module for front-end Dash functions."""


import logging
import time
from datetime import datetime as dt
from datetime import timezone as tz
from typing import cast, Collection, Dict, Final, List, Union

import dash  # type: ignore[import]
import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore[import]
import dash_html_components as html  # type: ignore[import]

from ..data_source import data_source as src
from ..data_source import table_config as tc
from ..utils.types import TSDCond

# constants
_RECENT_THRESHOLD: Final[float] = 1.0
REFRESH_MSG: Final[str] = "Refresh page and try again."


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


# --------------------------------------------------------------------------------------
# Component/Attribute-Constructor Functions


def new_data_button(id_num: int) -> html.Div:
    """Get a button for triggering adding of new data."""
    return html.Div(
        id=f"wbs-new-data-div-{id_num}",
        children=dbc.Button(
            "+ Add New Data",
            id=f"wbs-new-data-button-{id_num}",
            block=True,
            n_clicks=0,
            color=Color.DARK,
            disabled=False,
        ),
        hidden=True,
        className="table-tool-large",
    )


def table_columns(
    tconfig: tc.TableConfigParser, table_editable: bool
) -> List[Dict[str, object]]:
    """Grab table columns."""

    def _presentation(col_name: str) -> str:
        if tconfig.is_column_dropdown(col_name):
            return "dropdown"
        return "input"  # default

    def _type(col_name: str) -> str:
        if tconfig.is_column_numeric(col_name):
            return "numeric"
        return "any"  # default

    columns = [
        {
            "id": c,
            "name": c,
            "presentation": _presentation(c),
            "type": _type(c),
            "editable": table_editable and tconfig.is_column_editable(c),
            "hideable": True,
        }
        for c in tconfig.get_table_columns()
    ]

    return columns


def _style_cell_conditional_fixed_width(
    _id: str, width: str, border_left: bool = False, align_right: bool = False
) -> Dict[str, Collection[str]]:
    style = {
        "if": {"column_id": _id},
        "minWidth": width,
        "width": width,
        "maxWidth": width,
    }

    if border_left:
        style["border-left"] = "2.5px solid #23272B"

    if align_right:
        style["textAlign"] = "right"

    return style


def style_cell_conditional(
    tconfig: tc.TableConfigParser,
) -> List[Dict[str, Collection[str]]]:
    """Get the `style_cell_conditional` list.."""
    style_cell_conditional_list = []

    for col_name in tconfig.get_table_columns():
        # get values
        width = f"{tconfig.get_column_width(col_name)}px"
        border_left = tconfig.has_border_left(col_name)
        align_right = tconfig.is_column_numeric(col_name)

        # set & add style
        fixed_width = _style_cell_conditional_fixed_width(
            col_name, width, border_left=border_left, align_right=align_right
        )
        style_cell_conditional_list.append(fixed_width)

    return style_cell_conditional_list


def get_style_data_conditional(tconfig: tc.TableConfigParser) -> TSDCond:
    """Style Data..."""
    # zebra-stripe
    style_data_conditional = [
        {"if": {"row_index": "odd"}, "backgroundColor": "whitesmoke"},
    ]
    # stylize changed data
    # https://community.plotly.com/t/highlight-cell-in-datatable-if-it-has-been-edited/28808/3
    style_data_conditional += [
        {
            "if": {
                "column_id": col,
                "filter_query": f"{{{col}}} != {{{src.get_touchstone_name(col)}}}",
            },
            "fontWeight": "bold",
            # "color": "#258835",  # doesn't color dropdown-type value
            "fontStyle": "oblique",
        }
        for col in tconfig.get_table_columns()
    ]

    style_data_conditional += [
        {
            "if": {"state": "selected"},  # 'active' | 'selected'
            "backgroundColor": "transparent",
            "border": "2px solid #258835",
        },
        {
            "if": {"filter_query": "{Total Of?} contains 'GRAND TOTAL'"},
            "backgroundColor": "#258835",
            "color": "whitesmoke",
            "fontWeight": "bold",
        },
        {
            "if": {"filter_query": "{Total Of?} contains 'L2'"},
            "backgroundColor": "#23272B",
            "color": "whitesmoke",
            "fontWeight": "normal",
        },
        {
            "if": {"filter_query": "{Total Of?} contains 'L3'"},
            "backgroundColor": "#17a2b8",
            "color": "whitesmoke",
            "fontWeight": "normal",
        },
        {
            "if": {"filter_query": "{Total Of?} contains 'US TOTAL'"},
            "backgroundColor": "#9FA5AA",
            "color": "whitesmoke",
            "fontWeight": "normal",
        },
    ]

    return style_data_conditional


def deletion_toast() -> dbc.Toast:
    """Get a toast for confirming a deletion."""
    return dbc.Toast(
        id="wbs-deletion-toast",
        header="Deleted Record",
        is_open=False,
        dismissable=True,
        duration=0,  # 0 = forever
        fade=False,
        icon=Color.DARK,
        # top: 66 positions the toast below the navbar
        style={
            "position": "fixed",
            "top": 66,
            "right": 10,
            "width": 350,
            "font-size": "1.1em",
        },
        children=[
            html.Div(id="wbs-last-deleted-id"),
            html.Div(
                dbc.Button(
                    "Restore Row",
                    id="wbs-undo-last-delete",
                    color=Color.DANGER,
                    outline=True,
                ),
                style={"text-align": "center", "margin-top": "2rem"},
            ),
        ],
    )


def make_toast(
    header: str, message: Union[str, List[str]], icon_color: str, duration: float = 0,
) -> dbc.Toast:
    """Dynamically make a toast."""
    if isinstance(message, str):
        _messages = [message]
    else:
        _messages = message

    return dbc.Toast(
        id=f"wbs-toast-{get_now()}",
        header=header,
        is_open=True,
        dismissable=True,
        duration=duration * 1000,  # 0 = forever
        fade=False,
        icon=icon_color,
        # top: 66 positions the toast below the navbar
        style={
            "position": "fixed",
            "top": 66,
            "right": 10,
            "width": 350,
            "font-size": "1.1em",
        },
        children=[html.Div(m) for m in _messages],
    )


def upload_modal() -> dbc.Modal:
    """Get a modal for uploading an xlsx."""
    return dbc.Modal(
        id="wbs-upload-xlsx-modal",
        size="lg",
        is_open=False,
        backdrop="static",
        children=[
            dbc.ModalHeader("Override Live Table", className="caps"),
            dbc.ModalBody(
                children=[
                    dcc.Upload(
                        id="wbs-upload-xlsx",
                        children=html.Div(
                            ["Drag and Drop or ", html.A("Select Files")]
                        ),
                        style={
                            "width": "100%",
                            "height": "5rem",
                            "lineHeight": "5rem",
                            "borderWidth": "1px",
                            "borderStyle": "dashed",
                            "borderRadius": "5px",
                            "textAlign": "center",
                        },
                        # Allow multiple files to be uploaded
                        multiple=False,
                    ),
                    dbc.Alert(
                        id="wbs-upload-xlsx-filename-alert",
                        style={
                            "text-align": "center",
                            "margin-top": "1rem",
                            "margin-bottom": "0",
                        },
                    ),
                ]
            ),
            dbc.ModalFooter(
                children=[
                    dbc.Button(
                        "Cancel",
                        id="wbs-upload-xlsx-cancel",
                        n_clicks=0,
                        outline=True,
                        color=Color.DANGER,
                    ),
                    dcc.Loading(
                        type="default",
                        color="#258835",
                        children=[
                            dbc.Button(
                                "Override Live Table",
                                id="wbs-upload-xlsx-override-table",
                                n_clicks=0,
                                outline=True,
                                color=Color.SUCCESS,
                                disabled=True,
                            )
                        ],
                    ),
                ]
            ),
        ],
    )


def name_snapshot_modal() -> dbc.Modal:
    """Get a modal for selecting a snapshot."""
    return dbc.Modal(
        id="wbs-name-snapshot",
        size="sm",
        is_open=False,
        # backdrop="static",
        centered=True,
        children=[
            dbc.ModalBody(
                dcc.Input(
                    id="wbs-name-snapshot-input",
                    value="",
                    placeholder="Snapshot Name",
                    style={"width": "100%"},
                ),
            ),
            dbc.ModalFooter(
                dbc.Button(
                    "Name & Create",
                    id="wbs-name-snapshot-btn",
                    n_clicks=0,
                    color=Color.SUCCESS,
                )
            ),
        ],
    )
