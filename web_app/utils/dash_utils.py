"""Utility module for front-end Dash functions."""


import logging
from typing import Any, cast, Collection, Dict, Final, List, Union

import dash  # type: ignore[import]
import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore[import]
import dash_html_components as html  # type: ignore[import]
import dash_table  # type: ignore[import]
from flask_login import current_user  # type: ignore[import]

from ..data_source import data_source as src
from ..data_source import table_config as tc
from ..utils import types, utils

# constants
REFRESH_MSG: Final[str] = "Refresh page and try again."
GOOD_WAIT: Final[int] = 30
TEAL: Final[str] = "#17a2b8"
GREEN: Final[str] = "#258835"
TABLE_GRAY: Final[str] = "#23272B"
RELOAD: Final[str] = "location.reload();"


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


def triggered() -> str:
    """Return the component that triggered the callback.

    https://dash.plotly.com/advanced-callbacks
    """
    trig = dash.callback_context.triggered[0]["prop_id"]
    return cast(str, trig)


def triggered_id() -> str:
    """Return the component id that triggered the callback."""
    return triggered().split(".")[0]


def triggered_property() -> str:
    """Return the component property that triggered the callback."""
    return triggered().split(".")[1]


def flags_agree(one: bool, two: bool) -> bool:
    """Check if flags are the same (XNOR)."""
    if one == two:
        logging.warning(f"Flags agree {one=} {two=}")
    else:
        logging.warning(f"Flags disagree {one=} {two=}")
    return one == two


# --------------------------------------------------------------------------------------
# Callback Helper Functions


def get_sow_last_updated_label(
    table: types.Table, looking_at_snap: bool, tconfig: tc.TableConfigParser
) -> str:
    """Get the placeholder for the snapshots dropdown."""
    if looking_at_snap:
        return ""

    timestamps = [
        utils.iso_to_epoch(cast(str, r[tconfig.const.TIMESTAMP]))
        for r in table
        if r.get(tconfig.const.TIMESTAMP)
    ]

    if timestamps:
        most_recent = utils.get_human_time(max(timestamps))
    else:
        most_recent = utils.get_human_now()

    return f"SOWs Last Updated: {most_recent}"


def get_autosaved_labels(subject: str) -> List[html.Label]:
    """Return formatted labels for autosaving with datetime."""
    return [
        html.Label(f"{subject} Autosaved ✔", className="autosaved-label"),
        html.Label(utils.get_human_now(), className="autosaved-datetime"),
    ]


# --------------------------------------------------------------------------------------
# URL parsers


def get_wbs_l1(urlpath: str) -> str:
    """Get the WBS L1 from the url pathname."""
    try:
        return urlpath.split("/")[1]
    except IndexError:
        return ""


def get_inst(urlpath: str) -> str:
    """Get the institution from the url hash."""
    try:
        return urlpath.split("/")[2].upper()
    except IndexError:
        return ""


def build_urlpath(wbs_l1: str, inst: str = "") -> str:
    """Return a url pathname built from it pieces."""
    if wbs_l1:
        if inst:
            return f"{wbs_l1}/{inst.lower()}"
        return wbs_l1
    return ""


def need_user_redirect(urlpath: str) -> bool:
    """Return whether the user needs to be redirected."""
    return (
        current_user.is_authenticated
        and not current_user.is_admin
        and get_inst(urlpath) != current_user.institution
    )


# --------------------------------------------------------------------------------------
# Component/Attribute-Constructor Functions


def make_autosaved_container(id_: str) -> dcc.Loading:
    """Create a container for the autosaved container.

    Wrapped in a `dcc.Loading`.
    """
    return dcc.Loading(
        type="default",
        color=TEAL,
        children=html.Div(className="autosaved-container", id=id_),
    )


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
    tconfig: tc.TableConfigParser,
    table_editable: bool,
    is_institution_editable: bool = False,
) -> types.TColumns:
    """Grab table columns."""

    def _presentation(col_name: str) -> str:
        if tconfig.is_column_dropdown(col_name):
            return "dropdown"
        return "input"  # default

    def _type(col_name: str) -> str:
        if tconfig.is_column_numeric(col_name):
            return "numeric"
        return "any"  # default

    def _editable(col_name: str) -> bool:
        if (not is_institution_editable) and (col_name.lower() == "institution"):
            return False
        return table_editable and tconfig.is_column_editable(col_name)

    columns = [
        {
            "id": c,
            "name": c,
            "presentation": _presentation(c),
            "type": _type(c),
            "editable": _editable(c),
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
        style["border-left"] = f"2.5px solid {TABLE_GRAY}"

    if align_right:
        style["textAlign"] = "right"

    return style


def style_cell_conditional(tconfig: tc.TableConfigParser) -> types.TSCCond:
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


def get_table_tooltips(tconfig: tc.TableConfigParser) -> types.TTooltips:
    """Set tooltips for each column."""

    def _tooltip(column: str) -> str:
        tooltip = tconfig.get_column_tooltip(column)
        if not tconfig.is_column_editable(column) or tconfig.is_column_dropdown(column):
            return tooltip
        return f"{tooltip} (double-click to edit)"

    return {
        c: {"type": "text", "value": _tooltip(c), "delay": 250, "duration": None}
        for c in tconfig.get_table_columns()
    }


def get_style_data_conditional(tconfig: tc.TableConfigParser) -> types.TSDCond:
    """Style Data..."""
    # zebra-stripe
    style_data_conditional = [
        {"if": {"row_index": "odd"}, "backgroundColor": "whitesmoke"},
    ]

    # non-editable style
    style_data_conditional += [
        {
            "if": {"column_id": col},
            "color": "gray",
            "fontSize": "18",
            "fontStyle": "italic",
        }
        for col in tconfig.get_non_editable_columns()
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
            # "color": GREEN,  # doesn't color dropdown-type value
            "fontStyle": "oblique",
        }
        for col in tconfig.get_table_columns()
    ]

    # selected cell style
    style_data_conditional += [
        {
            "if": {"state": "selected"},  # 'active' | 'selected'
            "backgroundColor": "transparent",
            "border": f"2px solid {GREEN}",
        }
    ]

    # total row style
    style_data_conditional += [
        {
            "if": {"filter_query": "{Total-Row Description} contains 'GRAND TOTAL'"},
            "backgroundColor": GREEN,
            "color": "whitesmoke",
            "fontWeight": "bold",
            "fontStyle": "normal",
        },
        {
            "if": {"filter_query": "{Total-Row Description} contains 'L2'"},
            "backgroundColor": TABLE_GRAY,
            "color": "whitesmoke",
            "fontWeight": "normal",
            "fontStyle": "normal",
        },
        {
            "if": {"filter_query": "{Total-Row Description} contains 'L3'"},
            "backgroundColor": TEAL,
            "color": "whitesmoke",
            "fontWeight": "normal",
            "fontStyle": "normal",
        },
        {
            "if": {"filter_query": "{Total-Row Description} contains 'US TOTAL'"},
            "backgroundColor": "#9FA5AA",
            "color": "whitesmoke",
            "fontWeight": "normal",
            "fontStyle": "normal",
        },
    ]

    return style_data_conditional


def after_deletion_toast() -> dbc.Toast:
    """Get a toast for after a deletion."""
    return dbc.Toast(
        id="wbs-after-deletion-toast",
        header="Row Deleted",
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
        children=[html.Div(id="wbs-after-deletion-toast-message")],
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
        id=f"wbs-toast-{utils.get_now()}",
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
            html.Div(
                "Override All Institutions' SOW Tables with .xlsx",
                className="caps section-header",
            ),
            dbc.ModalBody(
                children=[
                    dcc.Upload(
                        id="wbs-upload-xlsx",
                        children=html.Div(["Drag and Drop or ", html.A("Select File")]),
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
                    html.Div(children=[]),
                    dbc.Button(
                        "Cancel",
                        id="wbs-upload-xlsx-cancel",
                        n_clicks=0,
                        outline=True,
                        color=Color.DANGER,
                    ),
                    dcc.Loading(
                        type="default",
                        color=GREEN,
                        children=[
                            dbc.Button(
                                "Override",
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


def upload_success_modal() -> dbc.Modal:
    """Get a modal for selecting a snapshot."""
    return dbc.Modal(
        id="wbs-upload-success-modal",
        size="md",
        is_open=False,
        backdrop="static",
        centered=True,
        children=[
            html.Div("Table Overridden", className="caps section-header"),
            dbc.ModalBody(id="wbs-upload-success-modal-body"),
            dbc.ModalFooter(
                dbc.Button(
                    "View Updated SOWs",
                    id="wbs-upload-success-view-new-table-button",
                    n_clicks=0,
                    block=True,
                    color=Color.SUCCESS,
                )
            ),
        ],
    )


def name_snapshot_modal() -> dbc.Modal:
    """Get a modal for selecting a snapshot."""
    return dbc.Modal(
        id="wbs-name-snapshot",
        size="md",
        is_open=False,
        # backdrop="static",
        centered=True,
        children=[
            html.Div("Collaboration-Wide Snapshot", className="section-header caps"),
            dbc.ModalBody(
                dcc.Input(
                    id="wbs-name-snapshot-input",
                    value="",
                    placeholder="Name",
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


def add_new_data_modal() -> dbc.Modal:
    """Get a modal for adding new data."""
    return dbc.Modal(
        id="wbs-new-data-modal",
        size="md",
        is_open=False,
        # backdrop="static",
        centered=True,
        children=[
            html.Div(
                children=dbc.Button(id="wbs-new-data-modal-dummy-add", n_clicks=0),
                hidden=True,
            ),
            html.Div(id="wbs-new-data-modal-header", className="section-header caps"),
            dbc.ModalBody(
                dcc.Textarea(
                    id="wbs-new-data-modal-task",
                    value="",
                    minLength=5,
                    placeholder="Enter Task Description",
                    style={"width": "100%"},
                ),
            ),
            dbc.ModalFooter(
                dbc.Button(
                    "+ Add",
                    id="wbs-new-data-modal-add-button",
                    n_clicks=0,
                    color=Color.SUCCESS,
                    className="table-tool-medium",
                ),
            ),
        ],
    )


def simple_table(id_: str) -> dash_table.DataTable:
    """Make a simple, read-only table."""
    return dash_table.DataTable(
        id=id_,
        editable=False,
        sort_action="native",
        style_table={"overflowX": "auto", "overflowY": "auto", "padding-left": "1em"},
        style_header={
            "backgroundColor": "black",
            "color": "whitesmoke",
            "whiteSpace": "normal",
            "fontWeight": "normal",
            "height": "auto",
            "fontSize": "10px",
            "lineHeight": "10px",
        },
        style_cell={
            "textAlign": "left",
            "fontSize": 14,
            "font-family": "sans-serif",
            "padding-left": "0.5em",
            "minWidth": "5px",
            "width": "5px",
            "maxWidth": "10px",
        },
        style_data={
            "whiteSpace": "normal",
            "height": "auto",
            "lineHeight": "20px",
            "wordBreak": "break-all",
        },
        export_format="xlsx",
        export_headers="display",
        merge_duplicate_headers=True,
        # https://community.plotly.com/t/rendering-all-rows-without-pages-in-datatable/15605/2
        page_size=9999999999,
    )


def fullscreen_loading(children: List[Any]) -> dcc.Loading:
    """Wrap components in a full-screen dcc.Loading component."""
    return dcc.Loading(
        type="cube",
        color=TEAL,
        fullscreen=True,
        style={"background": "transparent"},  # float atop all
        children=children,
    )
