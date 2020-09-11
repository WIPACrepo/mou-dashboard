"""Conditional in-cell drop-down menu with IceCube WBS MoU info."""

from typing import Collection, Dict, List, Optional, Tuple

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore[import]
import dash_html_components as html  # type: ignore[import]
import dash_table as dt  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]

from ..config import app
from ..utils import dash_utils as util
from ..utils import data_source as src
from ..utils.data_source import TableConfig
from ..utils.styles import CENTERED_100, WIDTH_45
from ..utils.types import DDCond, DDown, Record, SDCond, Table, TData

# --------------------------------------------------------------------------------------
# Layout


def _new_data_button(_id: str, block: bool = True) -> dbc.Button:
    return dbc.Button(
        "+ Add New Data",
        id=_id,
        block=block,
        n_clicks=0,
        color="secondary",
        disabled=True,
    )


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
        style["border-left"] = "1px solid black"

    if align_right:
        style["textAlign"] = "right"

    return style


def _style_cell_conditional(tconfig: TableConfig) -> List[Dict[str, Collection[str]]]:
    style_cell_conditional = []

    for col_name in tconfig.get_table_columns():
        # get values
        width = f"{tconfig.get_column_width(col_name)}px"
        border_left = tconfig.has_border_left(col_name)
        align_right = tconfig.is_column_numeric(col_name)

        # set & add style
        fixed_width = _style_cell_conditional_fixed_width(
            col_name, width, border_left=border_left, align_right=align_right
        )
        style_cell_conditional.append(fixed_width)

    return style_cell_conditional


def _get_style_data_conditional(tconfig: TableConfig) -> SDCond:
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
                "filter_query": util.get_changed_data_filter_query(col),
            },
            "fontWeight": "bold",
            # "color": "darkgreen",  # doesn't color dropdown-type value
            "fontStyle": "oblique",
        }
        for col in tconfig.get_table_columns()
    ]

    style_data_conditional += [
        {
            "if": {"state": "selected"},  # 'active' | 'selected'
            "backgroundColor": "transparent",
            "border": "2px solid darkgreen",
        },
    ]

    return style_data_conditional


def layout() -> html.Div:
    """Construct the HTML."""
    tconfig = TableConfig()

    return html.Div(
        children=[
            html.Div(
                # Institution Leader Sign-In
                children=[
                    html.H4("Institution Leader Sign-In"),
                    html.Div(
                        className="row",
                        style={"margin-left": "5%"},
                        children=[
                            dcc.Input(
                                id="tab-1-input-name",
                                value="",
                                type="text",
                                placeholder="name",
                                style={"width": "24%"},
                            ),
                            dcc.Input(
                                id="tab-1-input-email",
                                value="",
                                type="text",
                                placeholder="email",
                                style={"width": "23%"},
                            ),
                            html.I(
                                id="tab-1-name-email-icon",
                                n_clicks=0,
                                style={
                                    "margin-left": "0.5em",
                                    "align-text": "bottom",
                                    "fontSize": 25,
                                },
                            ),
                        ],
                    ),
                ],
            ),
            ####
            html.Hr(style={"margin-top": "3em", "margin-bottom": "3em"}),
            ####
            html.Div(
                style={"margin-bottom": "2em"},
                children=[
                    html.H4("Staffing Matrix Data"),
                    # SOW Filter
                    html.Div(
                        className="row",
                        style=CENTERED_100,
                        children=[
                            html.Div(
                                style=WIDTH_45,
                                children=[
                                    html.Div(children="Institution"),
                                    # Institution filter dropdown menu
                                    dcc.Dropdown(
                                        id="tab-1-filter-inst",
                                        options=[
                                            {"label": st, "value": st}
                                            for st in tconfig.get_institutions()
                                        ],
                                        value="",
                                        # multi=True
                                    ),
                                ],
                            ),
                            html.Div(
                                style=WIDTH_45,
                                children=[
                                    # Labor Category filter dropdown menu
                                    html.Div(children="Labor Category"),
                                    dcc.Dropdown(
                                        id="tab-1-filter-labor",
                                        options=[
                                            {"label": st, "value": st}
                                            for st in tconfig.get_labor_categories()
                                        ],
                                        value="",
                                        # multi=True
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            ####
            # html.Hr(style=SHORT_HR),
            ####
            html.Div(
                style=CENTERED_100,
                children=[
                    html.H6(
                        id="tab-1-how-to-edit-message", style={"font-style": "oblique"},
                    ),
                ],
            ),
            # Add Button
            html.Div(
                style={"margin-bottom": "0.8em"},
                children=[_new_data_button("tab-1-new-data-btn-top")],
            ),
            # Table
            dt.DataTable(
                id="tab-1-data-table",
                editable=False,
                # sort_action="native",
                # sort_mode="multi",
                # filter_action="native",  # the UI for native filtering isn't there yet
                sort_action="native",
                # Styles
                style_table={
                    "overflowX": "auto",
                    "overflowY": "auto",
                    "padding-left": "1em",
                },
                style_header={
                    "backgroundColor": "gainsboro",
                    "fontWeight": "bold",
                    "whiteSpace": "normal",
                    "height": "auto",
                    "lineHeight": "15px",
                },
                style_cell={
                    "textAlign": "left",
                    "fontSize": 14,
                    "font-family": "sans-serif",
                    "padding-left": "0.5em",
                    # these widths will make it obvious if there's a new/extra column
                    "minWidth": "10px",
                    "width": "10px",
                    "maxWidth": "10px",
                },
                style_cell_conditional=_style_cell_conditional(tconfig),
                style_data={
                    "whiteSpace": "normal",
                    "height": "auto",
                    "lineHeight": "20px",
                    "wordBreak": "normal",
                },
                style_data_conditional=_get_style_data_conditional(tconfig),
                # row_deletable set in callback
                # hidden_columns set in callback
                # page_size set in callback
                # data set in callback
                # columns set in callback
                # dropdown set in callback
                # dropdown_conditional set in callback
                export_format="xlsx",
                export_headers="display",
                merge_duplicate_headers=True,
                # fixed_rows={"headers": True, "data": 0},
            ),
            # Bottom Buttons
            html.Div(
                style={"margin-top": "0.8em"},
                children=[
                    # New Data
                    _new_data_button("tab-1-new-data-btn-bottom", block=False),
                    # Load Snapshot
                    dbc.Button(
                        "Load Snapshot",
                        id="tab-1-load-snapshot-button",
                        n_clicks=0,
                        outline=True,
                        color="info",
                        style={"margin-left": "1em"},
                    ),
                    # Make Snapshot
                    dbc.Button(
                        "Make Snapshot",
                        id="tab-1-make-snapshot-button",
                        n_clicks=0,
                        outline=True,
                        color="success",
                        style={"margin-left": "1em"},
                    ),
                    # Refresh
                    dbc.Button(
                        "↻",
                        id="tab-1-refresh-button",
                        n_clicks=0,
                        color="success",
                        style={"margin-left": "1em", "font-weight": "bold"},
                    ),
                    # Show All Rows
                    dbc.Button(
                        id="tab-1-show-all-rows-button",
                        n_clicks=0,
                        style={"margin-right": "1em", "float": "right"},
                    ),
                    # Show All Columns
                    dbc.Button(
                        id="tab-1-show-all-columns-button",
                        n_clicks=0,
                        style={"margin-right": "1em", "float": "right"},
                    ),
                ],
            ),
            # Dummy Label -- for communicating when table was last updated by an exterior control
            # NOTE: If table_data_exterior_controls() is called, then
            # NOTE:    table_data_interior_controls() is called next b/c table.data changes.
            # NOTE: A timestamp is the best way of stopping table_data_interior_controls().
            # NOTE:    A simple flag wouldn't work b/c table_data_interior_controls()
            # NOTE:    couldn't de-flag it (label can't be in multiple outputs).
            html.Label(
                "", id="tab-1-table-exterior-control-timestamp-dummy-label", hidden=True
            ),
        ]
    )


# --------------------------------------------------------------------------------------
# Table Callbacks


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-data-table", "data"),
        Output("tab-1-data-table", "active_cell"),
        Output("tab-1-data-table", "page_current"),
        Output("tab-1-table-exterior-control-timestamp-dummy-label", "children"),
    ],
    [
        Input("tab-1-filter-inst", "value"),
        Input("tab-1-filter-labor", "value"),
        Input("tab-1-new-data-btn-top", "n_clicks"),
        Input("tab-1-new-data-btn-bottom", "n_clicks"),
        Input("tab-1-refresh-button", "n_clicks"),
    ],
    [State("tab-1-data-table", "data"), State("tab-1-data-table", "columns")],
)  # pylint: disable=R0913
def table_data_exterior_controls(
    institution: str,
    labor: str,
    _: int,
    __: int,
    ___: int,
    state_data_table: TData,
    state_columns: List[Dict[str, str]],
) -> Tuple[TData, Optional[Dict[str, int]], int, str]:
    """Exterior control signaled that the table should be updated.

    This is either a filter, an "add new", or a refresh. Only "add new"
    changes MoU DS data. The others simply change what's visible to the
    user.
    """
    table: Table = []
    focus: Optional[Dict[str, int]] = {"row": 0, "column": 0}

    # Add New Data
    if util.triggered_id() in ["tab-1-new-data-btn-top", "tab-1-new-data-btn-bottom"]:
        table = state_data_table
        column_names = [c["name"] for c in state_columns]
        new_record: Record = {n: "" for n in column_names}

        # push to data source AND auto-fill labor and/or institution
        if new_record := src.push_record(new_record, labor=labor, institution=institution):  # type: ignore[assignment]
            new_record = util.add_original_copies_to_record(new_record, novel=True)
            table.insert(0, new_record)

    # Page Load or Filter or Refresh
    else:
        # focus on first cell, but not on page load
        if util.triggered_id() not in [
            "tab-1-filter-inst",
            "tab-1-filter-labor",
            "tab-1-refresh-button",
        ]:
            focus = None

        # pull from data source
        table = src.pull_data_table(institution=institution, labor=labor)
        table = util.add_original_copies(table)

    return table, focus, 0, util.get_now()


@app.callback(  # type: ignore[misc]
    Output("tab-1-data-table", "data_previous"),
    [Input("tab-1-data-table", "data")],
    [
        State("tab-1-data-table", "data_previous"),
        State("tab-1-table-exterior-control-timestamp-dummy-label", "children"),
    ],
)
def table_data_interior_controls(
    current_table: Table, previous_table: Table, table_exterior_control_ts: str,
) -> Table:
    """Interior control signaled that the table should be updated.

    This is either a row deletion or a field edit. The table's view has
    already been updated, so only DS communication is needed.

    NOTE: This function is also called following table_data_exterior_controls().
    This is unnecessary, so the timestamp of table_data_exterior_controls()'s
    last call will be checked to determine if that was indeed the case.
    """
    # On page load
    if not previous_table:
        return current_table

    # Don't call DS if the table was just updated via exterior controls
    if util.was_recent(table_exterior_control_ts):
        return current_table

    # Push modified records
    modified_records = [r for r in current_table if r not in previous_table]
    for record in modified_records:
        src.push_record(util.without_original_copies_from_record(record))

    # Delete deleted records
    mod_ids = [c["id"] for c in modified_records]
    deleted_records = [
        r
        for r in previous_table
        if (r not in current_table) and (r["id"] not in mod_ids)
    ]
    for record in deleted_records:
        src.delete_record(record)

    # Update data_previous
    return current_table


@app.callback(  # type: ignore[misc]
    Output("tab-1-data-table", "columns"), [Input("tab-1-data-table", "editable")],
)
def table_columns(table_editable: bool) -> List[Dict[str, object]]:
    """Grab table columns."""
    tconfig = TableConfig()

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


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-data-table", "dropdown"),
        Output("tab-1-data-table", "dropdown_conditional"),
    ],
    [Input("tab-1-data-table", "editable")],
)
def table_dropdown(_: bool) -> Tuple[DDown, DDCond]:
    """Grab table dropdowns."""
    simple_dropdowns: DDown = {}
    conditional_dropdowns: DDCond = []
    tconfig = TableConfig()

    def _options(menu: List[str]) -> List[Dict[str, str]]:
        return [{"label": m, "value": m} for m in menu]

    for col in tconfig.get_dropdown_columns():
        # Add simple dropdowns
        if tconfig.is_simple_dropdown(col):
            dropdown = tconfig.get_simple_column_dropdown_menu(col)
            simple_dropdowns[col] = {"options": _options(dropdown)}

        # Add conditional dropdowns
        elif tconfig.is_conditional_dropdown(col):
            # get dependee column and its options
            dep_col, dep_col_opts = tconfig.get_conditional_column_dependee(col)
            # make filter_query for each dependee-column option
            for opt in dep_col_opts:
                dropdown = tconfig.get_conditional_column_dropdown_menu(col, opt)
                conditional_dropdowns.append(
                    {
                        "if": {
                            "column_id": col,
                            "filter_query": f'''{{{dep_col}}} eq "{opt}"''',
                        },
                        "options": _options(dropdown),
                    }
                )

        # Error
        else:
            raise Exception(f"Dropdown column ({col}) is not simple nor conditional.")

    return simple_dropdowns, conditional_dropdowns


# --------------------------------------------------------------------------------------
# Other Callbacks


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-name-email-icon", "children"),
        Output("tab-1-data-table", "editable"),
        Output("tab-1-new-data-btn-top", "disabled"),
        Output("tab-1-new-data-btn-bottom", "disabled"),
        Output("tab-1-make-snapshot-button", "disabled"),
        Output("tab-1-how-to-edit-message", "children"),
        Output("tab-1-data-table", "row_deletable"),
    ],
    [Input("tab-1-input-name", "value"), Input("tab-1-input-email", "value")],
)
def sign_in(name: str, email: str) -> Tuple[str, bool, bool, bool, bool, str, bool]:
    """Enter name & email callback."""
    # TODO -- check auth

    if name and email:
        return (
            "✔",
            True,  # data-table editable
            False,  # new-data-button-top NOT disabled
            False,  # new-data-button-bottom NOT disabled
            False,  # make-snapshot-button NOT disabled
            "click a cell to edit",
            True,  # row is deletable
        )
    return (
        "✖",
        False,  # data-table NOT editable
        True,  # new-data-button-top disabled
        True,  # new-data-button-bottom disabled
        True,  # make-snapshot-button disabled
        "sign in to edit",
        False,  # row NOT deletable
    )


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-show-all-rows-button", "children"),
        Output("tab-1-show-all-rows-button", "color"),
        Output("tab-1-show-all-rows-button", "outline"),
        Output("tab-1-data-table", "page_size"),
        Output("tab-1-data-table", "page_action"),
    ],
    [Input("tab-1-show-all-rows-button", "n_clicks")],
)
def toggle_pagination(n_clicks: int) -> Tuple[str, str, bool, int, str]:
    """Toggle whether the table is paginated."""
    if n_clicks % 2 == 0:
        tconfig = TableConfig()
        return "Show All Rows", "secondary", True, tconfig.get_page_size(), "native"
    # https://community.plotly.com/t/rendering-all-rows-without-pages-in-datatable/15605/2
    return "Collapse Rows to Pages", "dark", False, 9999999999, "none"


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-show-all-columns-button", "children"),
        Output("tab-1-show-all-columns-button", "color"),
        Output("tab-1-show-all-columns-button", "outline"),
        Output("tab-1-data-table", "hidden_columns"),
    ],
    [Input("tab-1-show-all-columns-button", "n_clicks")],
)
def toggle_hidden_columns(n_clicks: int) -> Tuple[str, str, bool, List[str]]:
    """Toggle hiding/showing the default hidden columns."""
    if n_clicks % 2 == 0:
        tconfig = TableConfig()
        return "Show All Columns", "secondary", True, tconfig.get_hidden_columns()
    return "Show Default Columns", "dark", False, []
