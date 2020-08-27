"""Conditional in-cell drop-down menu with IceCube WBS MoU info."""

from typing import Any, Collection, Dict, List, Tuple, Union

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore[import]
import dash_html_components as html  # type: ignore[import]
import dash_table as dt  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]

from ..config import app
from ..utils import data
from ..utils.styles import CENTERED_100, WIDTH_45

# Types
SDict = Dict[str, str]



# --------------------------------------------------------------------------------------
# Layout


def _new_data_button(_id: str, block: bool = True) -> dbc.Button:
    return dbc.Button("+ Add New Data", id=_id, block=block, n_clicks=0, disabled=True)


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


def _new_data_modal() -> dbc.Modal:
    return dbc.Modal(
        id="tab-1-new-data-modal",
        size="lg",
        backdrop="static",
        children=[
            # Header
            dbc.ModalHeader("Add New Data"),
            # Body
            dbc.ModalBody(
                children=[  # "Data Added" confirmation label
                    dbc.Alert(
                        "Data Added ✔",
                        id="tab-1-added-alert-new-data-modal",
                        is_open=False,
                        color="success",
                        duration=4000,
                        style={
                            "font-size": "20px",
                            "font-style": "oblique",
                            "text-align": "center",
                        },
                    ),
                    html.Div(id="tab-1-form-new-data-modal"),
                ],
            ),
            # Footer
            dbc.ModalFooter(
                style={"display": "flex"},
                children=[
                    html.Div(
                        style={"width": "60%"},
                        children=[
                            dbc.Button(
                                "Cancel",
                                id="tab-1-cancel-new-data-modal",
                                className="ml-auto",
                                outline=True,
                                color="danger",
                            ),
                        ],
                    ),
                    # Save buttons
                    dbc.ButtonGroup(
                        style={
                            "width": "38%",
                            "display": "flex",
                            "flex-direction": "row",
                            "justify-content": "flex-end",
                        },
                        children=[
                            # "Add & Add Another" button
                            dbc.Button(
                                "Add & Add Another",
                                id="tab-1-add-&-add-another-new-data-modal",
                                className="ml-auto",
                                outline=True,
                                color="success",
                                style={"width": "60%"},
                            ),
                            # "Add & Exit" button
                            dbc.Button(
                                "Add & Exit",
                                id="tab-1-add-&-exit-new-data-modal",
                                className="ml-auto",
                                color="success",
                                style={"width": "40%"},
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


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
                                            for st in data.get_institutions()
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
                                            for st in data.get_labor()
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
                style_cell_conditional=[
                    {"if": {"column_id": "WBS L2"}, "padding-left": "1.5em"},
                    _style_cell_conditional_fixed_width("WBS L2", "225px"),
                    _style_cell_conditional_fixed_width(
                        "WBS L3", "225px", border_right=True
                    ),
                    _style_cell_conditional_fixed_width("US / Non-US", "65px"),
                    _style_cell_conditional_fixed_width("Institution", "85px"),
                    _style_cell_conditional_fixed_width("Labor Cat.", "85px"),
                    _style_cell_conditional_fixed_width("Names", "150px"),
                    _style_cell_conditional_fixed_width("Tasks", "300px"),
                    _style_cell_conditional_fixed_width(
                        "Source of Funds (U.S. Only)", "130px", border_right=True
                    ),
                    _style_cell_conditional_fixed_width("NSF M&O Core", "80px"),
                    _style_cell_conditional_fixed_width("NSF Base Grants", "80px"),
                    _style_cell_conditional_fixed_width(
                        "U.S. Institutional In-Kind", "80px"
                    ),
                    _style_cell_conditional_fixed_width(
                        "Europe & Asia Pacific In-Kind", "80px", border_right=True
                    ),
                    _style_cell_conditional_fixed_width("Grand Total", "80px"),
                ],
                style_data={
                    "whiteSpace": "normal",
                    "height": "auto",
                    "lineHeight": "20px",
                    "wordBreak": "normal",
                },
                # Page Size
                page_size=15,
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
                    _new_data_button("tab-1-new-data-button-bottom", block=False)
                ],
            ),
            # Modal for Adding New Data
            _new_data_modal(),
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
    ],
)
def table_data(
    institution: str, labor: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Collection[str]]]]:
    """Grab table data, optionally filter rows."""
    table = data.get_table(institution=institution, labor=labor)

    # Make hidden copy of each column to detect changed values
    for row in table:
        row.update({i + "_hidden": v for i, v in row.items()})

    # Style Data...
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
            "fontStyle": "oblique",
        }
        for i in data.get_table_columns()
    ]

    return table, style_data_conditional


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
def table_columns(_: bool) -> List[SDict]:
    """Grab table columns."""

    def _presentation(col_name: str) -> str:
        if data.is_column_dropdown(col_name):
            return "dropdown"
        return "input"

    columns = [
        {"id": c, "name": c, "presentation": _presentation(c)}
        for c in data.get_table_columns()
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

    for column in data.get_dropdown_columns():
        # Add simple dropdowns
        if data.is_simple_dropdown(column):
            simple_dropdowns[column] = {
                "options": [
                    {"label": i, "value": i}
                    for i in data.get_simple_column_dropdown_menu(column)
                ]
            }

        # Add conditional dropdowns
        elif data.is_conditional_dropdown(column):
            dependee_col_name, dependee_col_opts = data.get_conditional_column_dependee(
                column
            )
            for dependee_column_option in dependee_col_opts:
                conditional_dropdowns.append(
                    {
                        "if": {
                            "column_id": column,
                            "filter_query": f'''{{{dependee_col_name}}} eq "{dependee_column_option}"''',
                        },
                        "options": [
                            {"label": i, "value": i}
                            for i in data.get_conditional_column_dropdown_menu(
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
# "New Data" Modal Callbacks


@app.callback(
    Output("tab-1-new-data-modal", "is_open"),
    [
        Input("tab-1-new-data-button-top", "n_clicks"),
        Input("tab-1-new-data-button-bottom", "n_clicks"),
        Input("tab-1-cancel-new-data-modal", "n_clicks"),
        Input("tab-1-add-&-exit-new-data-modal", "n_clicks"),
    ],
    [State("tab-1-new-data-modal", "is_open")],
)  # type: ignore
def new_data_modal_open_close(
    open_clicks_1: int,
    open_clicks_2: int,
    cancel_clicks: int,
    add_exit_clicks: int,
    is_open: bool,
):
    """Open/close the "add new data" modal.

    If something was clicked -- change open/close state, otherwise...
    nothing was clicked (AKA on page launch) -- don't change state.
    """
    if open_clicks_1 or open_clicks_2 or cancel_clicks or add_exit_clicks:
        return not is_open
    return is_open


@app.callback(
    Output("tab-1-added-alert-new-data-modal", "is_open"),
    [Input("tab-1-add-&-add-another-new-data-modal", "n_clicks")],
    [State("tab-1-added-alert-new-data-modal", "is_open")],
)  # type: ignore
def new_data_modal_added_alert(add_another_clicks: int, is_open: bool) -> bool:
    """Save data from modal."""
    if add_another_clicks:
        # Button has never been clicked
        return not is_open
    return is_open


@app.callback(
    Output("tab-1-form-new-data-modal", "children"),
    [
        Input("tab-1-add-&-add-another-new-data-modal", "n_clicks"),
        Input("tab-1-add-&-exit-new-data-modal", "n_clicks"),
    ],
    [
        State("tab-1-form-new-data-modal", "children"),
        State("tab-1-added-alert-new-data-modal", "is_open"),
    ],
)  # type: ignore
def new_data_modal_add(
    add_another_clicks: int, add_exit_clicks: int, children: List[Any], is_open: bool
) -> List[Any]:
    """Save data from modal."""
    if not is_open:
        return []

    print("SAVE!")


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
    add_button_off = True
    table_editable = True

    if name and email:
        return (
            "✔",
            table_editable,
            not add_button_off,
            not add_button_off,
            "click a cell to edit",
        )
    return (
        "✖",
        not table_editable,
        add_button_off,
        add_button_off,
        "sign in to edit",
    )
