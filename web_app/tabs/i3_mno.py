"""Conditional in-cell drop-down menu with IceCube WBS MoU info."""

from typing import Any, cast, Collection, Dict, List, Tuple, Union

import dash  # type: ignore[import]
import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore[import]
import dash_html_components as html  # type: ignore[import]
import dash_table as dt  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]
from dash_table.Format import Format

from ..config import app
from ..utils import data_source
from ..utils.styles import CENTERED_100, WIDTH_45

# Types
SDict = Dict[str, str]
DTable = List[Dict[str, Any]]
SDCond = List[Dict[str, Collection[str]]]


# --------------------------------------------------------------------------------------
# Functions that really should be in a dash library


def _triggered() -> str:
    """https://dash.plotly.com/advanced-callbacks."""
    trig = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    return cast(str, trig)


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
    _id: str, width: str, border_right: bool = False
) -> Dict[str, Collection[str]]:
    style = {
        "if": {"column_id": _id},
        "minWidth": width,
        "width": width,
        "maxWidth": width,
    }

    if border_right:
        style["border-right"] = "1px solid black"

    return style


def _style_cell_conditional() -> List[Dict[str, Collection[str]]]:
    return [
        {"if": {"column_id": "WBS L2"}, "padding-left": "1.5em"},
        _style_cell_conditional_fixed_width("WBS L2", "225px"),
        _style_cell_conditional_fixed_width("WBS L3", "225px", border_right=True),
        _style_cell_conditional_fixed_width("US / Non-US", "65px"),
        _style_cell_conditional_fixed_width(data_source.INSTITUTION_LABEL, "85px"),
        _style_cell_conditional_fixed_width(data_source.LABOR_CAT_LABEL, "85px"),
        _style_cell_conditional_fixed_width("Names", "150px"),
        _style_cell_conditional_fixed_width("Tasks", "300px"),
        _style_cell_conditional_fixed_width(
            "Source of Funds (U.S. Only)", "130px", border_right=True
        ),
        _style_cell_conditional_fixed_width("NSF M&O Core", "80px"),
        _style_cell_conditional_fixed_width("NSF Base Grants", "80px"),
        _style_cell_conditional_fixed_width("U.S. Institutional In-Kind", "80px"),
        _style_cell_conditional_fixed_width(
            "Europe & Asia Pacific In-Kind", "80px", border_right=True
        ),
        _style_cell_conditional_fixed_width("Grand Total", "80px"),
    ]


def layout() -> html.Div:
    """Construct the HTML."""
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
                                    html.Div(children="Filter by Institution"),
                                    # Institution filter dropdown menu
                                    dcc.Dropdown(
                                        id="tab-1-filter-dropdown-inst",
                                        options=[
                                            {"label": st, "value": st}
                                            for st in data_source.get_institutions()
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
                                    html.Div(children="Filter by Labor Category"),
                                    dcc.Dropdown(
                                        id="tab-1-filter-dropdown-labor",
                                        options=[
                                            {"label": st, "value": st}
                                            for st in data_source.get_labor_categories()
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
                style={"margin-bottom": "0.5em"},
                children=[_new_data_button("tab-1-new-data-button-top")],
            ),
            # Table
            dt.DataTable(
                id="tab-1-data-table",
                editable=False,
                # sort_action="native",
                # sort_mode="multi",
                row_deletable=False,
                # Styles
                style_table={"overflowX": "auto", "overflowY": "auto"},
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
                style_cell_conditional=_style_cell_conditional(),
                style_data={
                    "whiteSpace": "normal",
                    "height": "auto",
                    "lineHeight": "20px",
                    "wordBreak": "normal",
                },
                # page_size set in callback
                # data set in callback
                # style_data_conditional set in callback
                # columns set in callback
                # dropdown set in callback
                # dropdown_conditional set in callback
            ),
            # Add Button
            html.Div(
                style={"margin-top": "0.5em"},
                children=[
                    _new_data_button("tab-1-new-data-button-bottom", block=False),
                    dbc.Button(
                        id="tab-1-show-all-button",
                        n_clicks=0,
                        style={"margin-left": "0.5em"},
                    ),
                ],
            ),
        ]
    )


# --------------------------------------------------------------------------------------
# Table Callbacks


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-data-table", "data"),
        Output("tab-1-data-table", "style_data_conditional"),
    ],
    [
        Input("tab-1-filter-dropdown-inst", "value"),
        Input("tab-1-filter-dropdown-labor", "value"),
        Input("tab-1-new-data-button-top", "n_clicks"),
        Input("tab-1-new-data-button-bottom", "n_clicks"),
    ],
    [State("tab-1-data-table", "data"), State("tab-1-data-table", "columns")],
)  # pylint: disable=R0913
def table_data(
    institution: str,
    labor: str,
    _: int,
    __: int,
    state_data_table: DTable,
    state_columns: List[Dict[str, str]],
) -> Tuple[DTable, SDCond]:
    """Grab table data, optionally filter rows."""

    def _get_style_data_conditional(columns: List[str]) -> SDCond:
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
                    "column_id": i,
                    "filter_query": "{{{0}}} != {{{0}_hidden}}".format(i),
                },
                "fontWeight": "bold",
                # "color": "darkgreen",  # doesn't color dropdown-type value
                "fontStyle": "oblique",
            }
            for i in columns
        ]
        return style_data_conditional

    # Add New Data
    if _triggered() in ["tab-1-new-data-button-top", "tab-1-new-data-button-bottom"]:
        # no data_source calls
        column_names = [c["name"] for c in state_columns]
        new_data_row = {n: "" for n in column_names}

        # add labor and/or institution, then push to data source
        if labor or institution:
            new_data_row[data_source.LABOR_CAT_LABEL] = labor
            new_data_row[data_source.INSTITUTION_LABEL] = institution
            data_source.push_data_row(new_data_row)

        # add to table and return
        state_data_table.insert(0, new_data_row)
        return state_data_table, _get_style_data_conditional(column_names)

    #
    # Else: Page Load
    table = data_source.pull_data_table(institution=institution, labor=labor)

    # Make a hidden copy of each column to detect changed values
    for row in table:
        row.update({i + "_hidden": v for i, v in row.items()})

    return table, _get_style_data_conditional(data_source.get_table_columns())


# @app.callback(  # type: ignore[misc]
#     Output("tab-1-data-table", "style_data_conditional"),
#     [Input("tab-1-data-table", "data")],
#     [State("tab-1-data-table", "style_data_conditional")],
# )
# def table_data_change(
#     data: str, style_data_conditional: List[Dict[str, SDict]]
# ) -> List[Dict[str, SDict]]:
#     """Grab table data, optionally filter rows."""
#     print(style_data_conditional)

#     if PREVIOUS_DATA:
#         pass

#     # PREVIOUS_DATA = data
#     return style_data_conditional


@app.callback(  # type: ignore[misc]
    Output("tab-1-data-table", "columns"), [Input("tab-1-data-table", "editable")],
)
def table_columns(table_editable: bool) -> List[SDict]:
    """Grab table columns."""

    def _presentation(col_name: str) -> str:
        if data_source.is_column_dropdown(col_name):
            return "dropdown"
        return "input"  # default

    def _type(col_name: str) -> str:
        if data_source.is_column_numeric(col_name):
            return "numeric"
        return "any"  # default

    columns = [
        {
            "id": c,
            "name": c,
            "presentation": _presentation(c),
            "type": _type(c),
            "format": Format(precision=2, scheme="f"),  # always 2 decimals
            "editable": table_editable and data_source.is_column_editable(c),
        }
        for c in data_source.get_table_columns()
    ]

    return columns


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-data-table", "dropdown"),
        Output("tab-1-data-table", "dropdown_conditional"),
    ],
    [Input("tab-1-data-table", "editable")],
)
def table_dropdown(
    _: bool,
) -> Tuple[
    Dict[str, Dict[str, List[SDict]]], List[Dict[str, Union[SDict, List[SDict]]]],
]:
    """Grab table dropdown."""
    simple_dropdowns = {}  # type: Dict[str, Dict[str, List[SDict]]]
    conditional_dropdowns = []  # type: List[Dict[str, Union[SDict, List[SDict]]]]

    for column in data_source.get_dropdown_columns():
        # Add simple dropdowns
        if data_source.is_simple_dropdown(column):
            simple_dropdowns[column] = {
                "options": [
                    {"label": i, "value": i}
                    for i in data_source.get_simple_column_dropdown_menu(column)
                ]
            }

        # Add conditional dropdowns
        elif data_source.is_conditional_dropdown(column):
            (
                dependee_col_name,
                dependee_col_opts,
            ) = data_source.get_conditional_column_dependee(column)
            for dependee_column_option in dependee_col_opts:
                conditional_dropdowns.append(
                    {
                        "if": {
                            "column_id": column,
                            "filter_query": f'''{{{dependee_col_name}}} eq "{dependee_column_option}"''',
                        },
                        "options": [
                            {"label": i, "value": i}
                            for i in data_source.get_conditional_column_dropdown_menu(
                                column, dependee_column_option
                            )
                        ],
                    }
                )

        # Error
        else:
            raise Exception(
                f"Dropdown column ({column}) is not simple nor conditional."
            )

    return simple_dropdowns, conditional_dropdowns


# --------------------------------------------------------------------------------------
# Other Callbacks


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-name-email-icon", "children"),
        Output("tab-1-data-table", "editable"),
        Output("tab-1-new-data-button-top", "disabled"),
        Output("tab-1-new-data-button-bottom", "disabled"),
        Output("tab-1-how-to-edit-message", "children"),
    ],
    [Input("tab-1-input-name", "value"), Input("tab-1-input-email", "value")],
)
def auth_updates(name: str, email: str) -> Tuple[str, bool, bool, bool, str]:
    """Enter name & email callback."""
    # TODO -- check auth

    if name and email:
        return (
            "✔",
            True,  # data-table editable
            False,  # new-data-button-top NOT disabled
            False,  # new-data-button-bottom NOT disabled
            "click a cell to edit",
        )
    return (
        "✖",
        False,  # data-table NOT editable
        True,  # new-data-button-top disabled
        True,  # new-data-button-bottom disabled
        "sign in to edit",
    )


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-show-all-button", "children"),
        Output("tab-1-show-all-button", "color"),
        Output("tab-1-data-table", "page_size"),
    ],
    [Input("tab-1-show-all-button", "n_clicks")],
)
def toggle_pagination(n_clicks: int) -> Tuple[str, str, int]:
    """Toggle whether the table is paginated."""
    if n_clicks % 2 == 0:
        return "Show All Rows", "light", 15
    # https://community.plotly.com/t/rendering-all-rows-without-pages-in-datatable/15605/2
    return "Collapse Rows to Pages", "dark", 9999999999
