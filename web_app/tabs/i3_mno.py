"""Conditional in-cell drop-down menu with IceCube WBS MoU info."""

from collections import OrderedDict
from typing import Dict, List, Tuple, Union

import dash  # type: ignore[import]

# --------------------------------------------------------------------------------------
# Layout
import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore[import]
import dash_html_components as html  # type: ignore[import]
import dash_table as dt  # type: ignore[import]
import pandas as pd  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]

from ..config import app
from ..utils.styles import (
    CENTERED_100,
    HIDDEN,
    SHORT_HR,
    WIDTH_22_5,
    WIDTH_30,
    WIDTH_45,
)

# --------------------------------------------------------------------------------------
# Constants

# read data from excel file
DF = pd.read_excel("WBS.xlsx").fillna("")

# Institutions and Labor Categories filter dropdown menus
INSTITUTIONS = [i for i in DF["Institution"].unique().tolist() if i]
print(f"INSTITUTIONS: {INSTITUTIONS}")
LABOR = [b for b in DF["Labor Cat."].unique().tolist() if b]
print(f"LABOR: {LABOR}")

# # In-cell WBS L2/L3 dropdown menu
DF_PER_ROW_DROPDOWN = pd.DataFrame(
    OrderedDict(
        [
            (
                # WBS L2 dropdown menu
                "WBS L2",
                [
                    "2.1 Program Coordination",
                    "2.2 Detector Operations & Maintenance (Online)",
                    "2.3 Computing & Data Management Services",
                    "2.4 Data Processing & Simulation Services",
                    "2.5 Software",
                    "2.6 Calibration",
                ],
            ),
            (
                # WBS L3 dropdown menu
                "WBS L3",
                [
                    "2.1.1 Administration",
                    "2.2.1 Run Coordination",
                    "2.3.1 Data Storage & Transfer",
                    "2.4.1 Offline Data Production",
                    "2.5.1 Core Software",
                    "2.6.1 Detector Calibration",
                ],
            ),
            # Source of funds dropdown menu
            (
                "Source of Funds (U.S. Only)",
                [
                    "NSF M&O Core",
                    "Base Grants",
                    "US In-Kind",
                    "Non-US In-kind",
                    "Non-US In-kind",
                    "Non-US In-kind",
                ],
            ),
        ]
    )
)  # df_per_row_dropdown


def _get_add_button(_id: str, block: bool = True) -> dbc.Button:
    return dbc.Button("+ Add New Data", id=_id, block=block, n_clicks=0, disabled=True)


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
                                            for st in INSTITUTIONS
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
                                            {"label": st, "value": st} for st in LABOR
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
                children=[_get_add_button("tab-1-editing-rows-button-top")],
            ),
            # Table
            dt.DataTable(
                id="tab-1-dropdown-per-row",
                editable=False,
                row_deletable=False,
                # data set in callback
                columns=(
                    [
                        {
                            "id": "WBS L2",
                            "name": "WBS L2 (new)",
                            "presentation": "dropdown",
                        },
                        {
                            "id": "WBS L3",
                            "name": "WBS L3 (new)",
                            "presentation": "dropdown",
                        },
                        {
                            "id": "Source of Funds (U.S. Only)",
                            "name": "Source of Funds (U.S. Only)",
                            "presentation": "dropdown",
                        },
                    ]
                    + [{"id": c, "name": c} for c in DF.columns]
                ),
                # Styles
                style_table={"overflowX": "scroll"},
                style_cell={
                    "textAlign": "left",
                    "fontSize": 14,
                    "font-family": "sans-serif",
                    "padding-left": "0.5em",
                },
                style_cell_conditional=[
                    {"if": {"column_id": "WBS L2"}, "padding-left": "1.5em"}
                ],
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "whitesmoke"}
                ],
                style_header={"backgroundColor": "gainsboro", "fontWeight": "bold"},
                # Dropdowns
                dropdown={
                    "WBS L2": {
                        "options": [
                            {"label": i, "value": i}
                            for i in DF_PER_ROW_DROPDOWN["WBS L2"].unique()
                        ]
                    },
                    "Source of Funds (U.S. Only)": {
                        "options": [
                            {"label": i, "value": i}
                            for i in DF_PER_ROW_DROPDOWN[
                                "Source of Funds (U.S. Only)"
                            ].unique()
                        ]
                    },
                },
                # Page Size
                page_size=20,
            ),
            # Add Button
            html.Div(style={"margin-top": "0.5em"}, children=[ADD_BUTTON]),
        ]
    )


# --------------------------------------------------------------------------------------
# Static Callbacks


@app.callback(
    Output("tab-1-dropdown-per-row", "dropdown_conditional"),
    [Input("tab-1-dropdown-per-row", "editable")],
)  # type: ignore[misc]
def get_dropdown_conditional(
    editable: bool,
) -> List[Dict[str, Union[Dict[str, str], List[Dict[str, str]]]]]:
    """Return the conditional filterings for the drop-down menu."""
    return [
        {
            "if": {
                "column_id": "WBS L3",
                "filter_query": '{WBS L2} eq "2.1 Program Coordination"',
            },
            "options": [
                {"label": i, "value": i}
                for i in [
                    "2.1.0 Program Coordination",
                    "2.1.1 Administration",
                    "2.1.2 Engineering and R&D Support",
                    "2.1.3 USAP Support & Safety",
                    "2.1.4 Education & Outreach",
                    "2.1.5 Communications",
                ]
            ],
        },
        {
            "if": {
                "column_id": "WBS L3",
                "filter_query": '{WBS L2} eq "2.2 Detector Operations & Maintenance (Online)"',
            },
            "options": [
                {"label": i, "value": i}
                for i in [
                    "2.2.0 Detector Operations & Maintenance",
                    "2.2.1 Run Coordination",
                    "2.2.2 Data Acquisition",
                    "2.2.3 Online Filter (PnF)",
                    "2.2.4 Detector Monitoring",
                    "2.2.5 Experiment Control",
                    "2.2.6 Surface Detectors",
                    "2.2.7 Supernova System",
                    "2.2.8 Real-Time Alerts",
                    "2.2.9 SPS/SPTS",
                ]
            ],
        },
        {
            "if": {
                "column_id": "WBS L3",
                "filter_query": '{WBS L2} eq "2.3 Computing & Data Management Services"',
            },
            "options": [
                {"label": i, "value": i}
                for i in [
                    "2.3.0 Computing & Data Management Services",
                    "2.3.1 Data Storage & Transfer",
                    "2.3.2 Core Data Center Infrastructure",
                    "2.3.3 Central Computing Resources",
                    "2.3.4 Distributed Computing Resources",
                ]
            ],
        },
        {
            "if": {
                "column_id": "WBS L3",
                "filter_query": '{WBS L2} eq "2.4 Data Processing & Simulation Services"',
            },
            "options": [
                {"label": i, "value": i}
                for i in [
                    "2.4.0 Data Processing & Simulation Services",
                    "2.4.1 Offline Data Production",
                    "2.4.2 Simulation Production",
                    "2.4.3 Public Data Products",
                ]
            ],
        },
        {
            "if": {
                "column_id": "WBS L3",
                "filter_query": '{WBS L2} eq "2.5 Software"',
            },
            "options": [
                {"label": i, "value": i}
                for i in [
                    "2.5.0 Software",
                    "2.5.1 Core Software",
                    "2.5.2 Simulation Software",
                    "2.5.3 Reconstruction",
                    "2.5.4 Science Support Tools",
                    "2.5.5 Software Development Infrastructure",
                ]
            ],
        },
        {
            "if": {
                "column_id": "WBS L3",
                "filter_query": '{WBS L2} eq "2.6 Calibration"',
            },
            "options": [
                {"label": i, "value": i}
                for i in [
                    "2.6.0 Calibration",
                    "2.6.1 Detector Calibration",
                    "2.6.2 Ice Properties",
                ]
            ],
        },
    ]


# --------------------------------------------------------------------------------------
# Callbacks

# --------------------------------------------------------------------------------------
# Other Callbacks


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-name-email-icon", "children"),
        Output("tab-1-dropdown-per-row", "editable"),
        Output("tab-1-editing-rows-button-top", "disabled"),
        Output("tab-1-editing-rows-button-bottom", "disabled"),
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


@app.callback(  # type: ignore[misc]
    Output("tab-1-dropdown-per-row", "data"),
    [
        Input("tab-1-filter-dropdown-inst", "value"),
        Input("tab-1-filter-dropdown-labor", "value"),
    ],
    [
        State("tab-1-dropdown-per-row", "data"),
        State("tab-1-dropdown-per-row", "columns"),
    ],
)
def table_data(
    institution: List[Dict[str, str]],
    labor: str,
    rows: str,
    columns: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """Filter dropdown menu & new rows callbacks."""
    print("HAAAANNNNKKK")

    dff = DF
    # filter by labor
    if labor:
        dff = dff[dff["Labor Cat."] == labor]

    # filter by institution
    if institution:
        dff = dff[dff["Institution"] == institution]

    return dff.to_dict("records")
