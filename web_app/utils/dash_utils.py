"""Utility module for front-end Dash functions."""


import logging
import urllib
from typing import Any, Collection, Dict, Final, List, Union, cast

import dash  # type: ignore[import]
import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore[import]
import dash_html_components as html  # type: ignore[import]
import dash_table  # type: ignore[import]

from ..data_source import data_source as src
from ..data_source import institution_info
from ..data_source import table_config as tc
from ..utils import types, utils
from ..utils.oidc_tools import CurrentUser

# constants
REFRESH_MSG: Final[str] = "Refresh page and try again."
GOOD_WAIT: Final[int] = 30
TEAL: Final[str] = "#17a2b8"
GREEN: Final[str] = "#258835"
RED: Final[str] = "#B22222"
YELLOW: Final[str] = "#EED202"
LIGHT_YELLOW: Final[str] = "#FFEC82"
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

    return most_recent


def timecheck_labels(
    subject: str, verbage: str, snap_ts: types.DashVal = None
) -> List[html.Label]:
    """Return labels with datetime and a checkmark for saved/submitted/etc."""
    if snap_ts:
        return []
    return [
        html.Label(f"{subject} {verbage} ✔", className="timecheck-label"),
        html.Label(utils.get_human_now(), className="timecheck-datetime"),
    ]


HEADCOUNTS_REQUIRED = [
    html.Label(
        "Headcounts are required. Please enter all four numbers.",
        style={"color": "red", "font-weight": "bold"},
    )
]


def counts_saved_label(
    confirmed: bool, just_now_confirmed: bool, label: str
) -> List[html.Label]:
    """Get a counts saved-label."""
    if just_now_confirmed:  # show saved label if count was just now confirmed
        return timecheck_labels(label, "Submitted")
    elif not confirmed:  # if it's not confirmed, then don't show anything
        return []
    else:  # it's confirmed but this isn't new, so don't change anything
        return dash.no_update  # type: ignore[no-any-return]


def _figure_counts_confirmation_state(
    confirm_trigger_id: str, prev_state: bool, causal_fields: List[str]
) -> bool:
    if triggered_id() == confirm_trigger_id:
        # the user is confirming the count
        return True
    elif triggered_id() in causal_fields:
        # if a casual-field value changed, then the count is no longer confirmed
        return False
    else:
        # an unrelated value changed, so maintain previous state
        return prev_state


def figure_headcounts_confirmation_state(prev_state: bool) -> bool:
    """Figure the confirmation states for the headcounts."""
    return _figure_counts_confirmation_state(
        "wbs-headcounts-confirm-yes",
        prev_state,
        [
            "wbs-phds-authors",
            "wbs-faculty",
            "wbs-scientists-post-docs",
            "wbs-grad-students",
        ],
    )


def figure_computing_confirmation_state(prev_state: bool) -> bool:
    """Figure the confirmation states for the computing counts."""
    return _figure_counts_confirmation_state(
        "wbs-computing-confirm-yes", prev_state, ["wbs-cpus", "wbs-gpus"]
    )


# --------------------------------------------------------------------------------------
# URL parsers


def get_wbs_l1(urlpath: str) -> str:
    """Get the WBS L1 from the url pathname."""
    try:
        return urllib.parse.unquote(urlpath).split("/")[1]
    except IndexError:
        return ""


def get_inst(urlpath: str) -> str:
    """Get the institution from the url hash."""
    try:
        # insts & url are case-sensitive
        return urllib.parse.unquote(urlpath).split("/")[2]
    except IndexError:
        return ""


def build_urlpath(wbs_l1: str, inst: str = "") -> str:
    """Return a url pathname built from it pieces."""
    if wbs_l1:
        if inst:
            return f"{wbs_l1}/{inst}"
        return wbs_l1
    return ""


def user_viewing_wrong_inst(urlpath: str) -> bool:
    """Return whether the user needs to be redirected.

    Assumes the user is logged in.
    """
    if CurrentUser.is_admin():
        all_insts = list(institution_info.get_institutions_infos().keys())
        return get_inst(urlpath) not in all_insts + [""]
    else:
        return get_inst(urlpath) not in CurrentUser.get_institutions()


def root_is_not_wbs(s_urlpath: str) -> bool:
    """Return whether the root is not a legit."""
    return get_wbs_l1(s_urlpath) not in ["mo", "upgrade"]


class CallbackAbortException(Exception):
    """Raised when there's a reason to abort a callback."""


def precheck_setup_callback(s_urlpath: str) -> None:
    """Return whether to abort a dash setup callback."""
    if triggered_id():  # Guarantee this is the initial call
        raise Exception(f"Setup-callback was called after setup ({triggered_id()=})")

    # Check if legit full-fledged path (otherwise a redirect is happening soon)
    if root_is_not_wbs(s_urlpath):
        raise CallbackAbortException(f"Bad URL: {s_urlpath}")

    # Check Login
    if not CurrentUser.is_loggedin_with_permissions():
        raise CallbackAbortException(f"Bad permissions: {s_urlpath}")

    if user_viewing_wrong_inst(s_urlpath):
        raise CallbackAbortException(f"Bad institution: {s_urlpath}")


# --------------------------------------------------------------------------------------
# Component/Attribute-Constructor Functions


def make_timecheck_container(id_: str, loading: bool = False) -> html.Div:
    """Create a container for the timecheck container.

    Optionally, wrapped in a `dcc.Loading`.
    """
    if loading:
        return dcc.Loading(
            type="default",
            color=TEAL,
            children=html.Div(className="timecheck-container", id=id_),
        )
    else:
        return html.Div(className="timecheck-container", id=id_)


def make_confirm_container(id_subject: str, button_label: str) -> html.Div:
    """Create a container for confirming `subject`."""
    return html.Div(
        id=f"wbs-{id_subject}-confirm-container",
        hidden=True,
        className="timecheck-container",
        children=dbc.Button(button_label, id=f"wbs-{id_subject}-confirm-yes"),
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
        c: {"type": "text", "value": _tooltip(c), "delay": 1500, "duration": 2000}
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

    # incomplete rows
    style_data_conditional += [
        {"if": {"filter_query": f'{{{col}}} = ""'}, "backgroundColor": LIGHT_YELLOW}
        for col in tconfig.get_table_columns()
        if col not in tconfig.get_hidden_columns()
    ]

    # selected cell style
    style_data_conditional += [
        {
            "if": {"state": "selected"},  # 'active' | 'selected'
            "backgroundColor": "transparent",
            "border": f"2px solid {GREEN}",
        }
    ]

    # total-row style
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
    header: str,
    message: Union[str, List[str]],
    icon_color: str,
    duration: float = 0,
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


# def add_new_data_modal() -> dbc.Modal:
#     """Get a modal for adding new data."""
#     return dbc.Modal(
#         id="wbs-new-data-modal",
#         size="md",
#         is_open=False,
#         # backdrop="static",
#         centered=True,
#         children=[
#             html.Div(
#                 children=dbc.Button(id="wbs-new-data-modal-dummy-add", n_clicks=0),
#                 hidden=True,
#             ),
#             html.Div(id="wbs-new-data-modal-header", className="section-header caps"),
#             dbc.ModalBody(
#                 dcc.Textarea(
#                     id="wbs-new-data-modal-task",
#                     value="",
#                     minLength=5,
#                     placeholder="Enter Task Description",
#                     style={"width": "100%"},
#                 ),
#             ),
#             dbc.ModalFooter(
#                 dbc.Button(
#                     "+ Add",
#                     id="wbs-new-data-modal-add-button",
#                     n_clicks=0,
#                     color=Color.SUCCESS,
#                     className="table-tool-medium",
#                 ),
#             ),
#         ],
#     )


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
