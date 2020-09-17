#!/usr/bin/env python3
"""MoU Dashboard application."""

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore
import dash_html_components as html  # type: ignore
from dash.dependencies import Input, Output  # type: ignore

from .config import app
from .tabs import i3_mno
from .utils.styles import CONTENT_STYLE, TAB_SELECTED_STYLE, TAB_STYLE, TABS_STYLE

app.layout = html.Div(
    style={
        "padding-left": "5%",
        "padding-right": "5%",
        "backgroundColor": "lightgrey",
    },
    children=[
        dbc.Row(
            [
                html.Label(
                    children="MoU", className="title", style={"align-text": "bottom"}
                ),
                html.Div(
                    html.Label(
                        children="Dashboard",
                        className="titleb",
                        style={"align-text": "bottom"},
                    ),
                    style={
                        "display": "flex",
                        "border": "2.5px solid #23272B",
                        "margin-top": "2.4rem",
                        "margin-left": "0.25rem",
                        "height": "3rem",
                        "border-radius": ".25rem",
                    },
                ),
            ],
            justify="start",
            style={"display": "flex"},
        ),
        html.Div(
            style={"backgroundColor": "whitesmoke"},
            children=[
                dcc.Tabs(
                    id="mou-dash-tabs",
                    value="tab1",
                    style=TABS_STYLE,
                    children=[
                        dcc.Tab(
                            label="IceCube M&O",
                            value="tab1",
                            style=TAB_STYLE,
                            selected_style=TAB_SELECTED_STYLE,
                        ),
                        dcc.Tab(
                            label="Upgrade M&O",
                            value="tab2",
                            style=TAB_STYLE,
                            selected_style=TAB_SELECTED_STYLE,
                            disabled=True,
                            disabled_style=TAB_STYLE,
                        ),
                    ],
                ),
                html.Div(id="tab-content", style=CONTENT_STYLE),
            ],
        ),
    ],
)


@app.callback(
    Output("tab-content", "children"), [Input("mou-dash-tabs", "value")]
)  # type: ignore
def render_content(tab: str) -> html.Div:
    """Create HTML for tab."""
    layouts = {"tab1": i3_mno.layout}

    return layouts[tab]()
