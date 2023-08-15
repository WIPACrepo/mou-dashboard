"""Utility module for front-end Dash functions."""


import logging
import urllib
from typing import Any, Collection, Dict, Final, List, cast

import dash_bootstrap_components as dbc  # type: ignore[import]
import universal_utils.types as uut
from dash import callback_context, dash_table, dcc, html  # type: ignore[import]

from ..data_source import connections
from ..data_source import data_source as src
from ..data_source import table_config as tc
from ..data_source.connections import CurrentUser
from ..utils import types, utils

# constants
REFRESH_MSG: Final[str] = "Refresh page and try again."
GOOD_WAIT: Final[int] = 30
TEAL: Final[str] = "#17a2b8"
GREEN: Final[str] = "#258835"
RED: Final[str] = "#B22222"
YELLOW: Final[str] = "#EED202"
LIGHT_YELLOW: Final[str] = "#FFEC82"
TABLE_GRAY: Final[str] = "black"  # "#23272B"
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

    @staticmethod
    def to_hex(color: str) -> str:
        """Get hex color for each `Color` color."""
        match color:
            case Color.PRIMARY:
                return "#0d6efd"
            case Color.SECONDARY:
                return "#6c757d"
            case Color.SUCCESS:
                return "#198754"
            case Color.INFO:
                return "#0dcaf0"
            case Color.WARNING:
                return "#ffc107"
            case Color.DANGER:
                return "#dc3545"
            case Color.LIGHT:
                return "#f8f9fa"
            case Color.DARK:
                return "#212529"
        return "black"


class IconClassNames:
    """Icon class names."""

    CLOUD = "fa-solid fa-cloud"
    CLOCK_ROTATE_LEFT = "fa-solid fa-clock-rotate-left"
    RIGHT_TO_BRACKET = "fa-solid fa-right-to-bracket"
    PEN_TO_SQUARE = "fa-solid fa-pen-to-square"
    CHECK_TO_SLOT = "fa-solid fa-check-to-slot"
    CHECK = "fa-solid fa-check"
    LAYER_GROUP = "fa-solid fa-layer-group"
    TABLE_COLUMNS = "fa-solid fa-table-columns"
    CALCULATOR = "fa-solid fa-calculator"
    PLUS_MINUS = "fa-solid fa-plus-minus"


# --------------------------------------------------------------------------------------
# Function(s) that really should be in a dash library


def triggered() -> str:
    """Return the component that triggered the callback.

    https://dash.plotly.com/advanced-callbacks
    """
    trig = callback_context.triggered[0]["prop_id"]
    return cast(str, trig)


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
    table: uut.WebTable, looking_at_snap: bool, tconfig: tc.TableConfigParser
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


HEADCOUNTS_REQUIRED = [
    html.Label(
        "Headcounts are required. Please enter all four numbers.",
        style={"color": "red", "font-weight": "bold"},
    )
]


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


def build_urlpath(wbs_l1: str, inst: str | None = "") -> str:
    """Return a url pathname built from it pieces.

    url: [<WBS_L1>[/<INST>]]
    """
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
        all_insts = list(connections.get_institutions_infos().keys())
        return get_inst(urlpath) not in all_insts + [""]
    else:
        return get_inst(urlpath) not in CurrentUser.get_institutions()


def root_is_not_wbs(s_urlpath: str) -> bool:
    """Return whether the root is not a legit."""
    return get_wbs_l1(s_urlpath) not in ["mo", "upgrade"]


class CallbackAbortException(Exception):
    """Raised when there's a reason to abort a callback."""


def precheck_setup_callback(s_urlpath: str) -> None:
    """Return whether to abort a dash setup callback based on url & user permissions."""
    if triggered() != ".":  # Guarantee this is the initial call
        raise Exception(f"Setup-callback was called after setup ({triggered()=})")

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


class ButtonIconLabelTooltipFactory:
    """For making a button comprising of an icon and label, with a tooltip bubble."""

    @staticmethod
    def build_classname(outline: bool, color: str = Color.SECONDARY) -> str:

        if outline:
            btn_class = f"btn-outline-{color}"
        else:
            btn_class = f"btn-{color}"

        return f"button-icon-label caps btn {btn_class} cursor-pointer"

    @staticmethod
    def make(
        parent_id: str,
        icon_class: str = "",
        label_text: str = "",
        tooltip_text: str = "",
        button_classname: str = "",
        hidden: bool = False,
        float_right: bool = False,
        add_interval: bool = False,
        add_loading: bool = False,
        width: str | None = None,
        height: str | None = None,
        loading_color: str = Color.SECONDARY,
        border_width: int | None = None,
        border_radius: str | None = None,
    ) -> html.Div:
        """Make a button comprising of an icon and label, with a tooltip bubble."""
        div_style: Dict[str, uut.StrNum] = {
            "display": "flex",
            "justify-content": "center",
        }
        if float_right:
            div_style["float"] = "right"
        if border_width is not None:
            div_style["border"] = border_width
        if border_radius is not None:
            div_style["border-radius"] = border_radius
        if width:
            div_style["width"] = width
        if height:
            div_style["height"] = height
        # div_style["height"] = "100%"

        cursor_class = "cursor-pointer"

        # All the stuff that goes into the button
        div_children = [
            html.Div(
                style={"width": "2rem"},
                className=cursor_class,
                children=html.I(id=f"{parent_id}-i", className=icon_class),
            ),
            html.Div(
                style={"text-align": "left"},
                children=html.Label(
                    id=f"{parent_id}-label",
                    children=label_text,
                    className=cursor_class,
                ),
            ),
            dbc.Tooltip(
                id=f"{parent_id}-tooltip",
                children=tooltip_text,
                target=parent_id,
                placement="auto",
                style={"font-size": 12},
            ),
        ]
        if add_interval:
            div_children.append(
                dcc.Interval(id=f"{parent_id}-interval", interval=60 * 1000)
            )

        if not button_classname:
            button_classname = ButtonIconLabelTooltipFactory.build_classname(
                outline=True
            )

        # Build the button
        div = html.Div(
            id=parent_id,
            n_clicks=0,
            hidden=hidden,
            className=button_classname,
            style=div_style,
            children=div_children,
        )

        # Optionally wrap it in a dcc.Loading
        if add_loading:
            return dcc.Loading(
                type="circle",
                parent_style=div_style,
                color=Color.to_hex(loading_color),
                children=div,
            )
        return div


def make_stacked_label_component_float_left(
    component: Any, width: int = 0, label: str | None = None
) -> html.Div:
    """Stack a label on top of a component and put it in a html.Div floating left."""
    label_style = {}
    if not label:
        label = "."
        label_style = {"opacity": 0}

    return html.Div(
        style={"float": "left", "width": f"{width}rem"},
        children=[
            html.Div(
                label,
                className="caps",
                style=label_style,
            ),
            component,
        ],
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
        if col in tconfig.get_mandatory_columns()
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
        icon=Color.DARK,
        # top: 66 positions the toast below the navbar
        style={
            "position": "fixed",
            "top": 66,
            "right": 10,
            "width": 350,
            "font-size": "12px",
        },
        children=[html.Div(id="wbs-after-deletion-toast-message")],
    )


def make_toast(
    header: str,
    message: str | List[str],
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
        icon=icon_color,
        # top: 66 positions the toast below the navbar
        style={
            "position": "fixed",
            "top": 66,
            "right": 10,
            "width": 350,
            "font-size": "12px",
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
                "Override All Institutions' Statements of Work with .xlsx",
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
                html.Div(
                    className="d-grid gap-2",
                    children=dbc.Button(
                        "View Updated SOWs",
                        id="wbs-upload-success-view-new-table-button",
                        n_clicks=0,
                        color=Color.SUCCESS,
                    ),
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
            "lineHeight": "12px",
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
