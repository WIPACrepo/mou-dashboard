#!/usr/bin/env python3
"""MoU Dashboard application."""

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore
import dash_html_components as html  # type: ignore
from dash.dependencies import Input, Output  # type: ignore

from .config import app
from .tabs import i3_mno

# Layout
app.layout = html.Div(
    className="background",
    children=[
        # Title
        dbc.Row(
            justify="start",
            style={"display": "flex"},
            children=[
                html.Label("MoU", className="mou-title"),
                html.Label("Dash", className="dashboard-title dash-title",),
                html.Label("board", className="dashboard-title board-title",),
            ],
        ),
        # Tabs
        dcc.Tabs(
            id="mou-dash-tabs",
            value="tab1",
            children=[
                dcc.Tab(label="IceCube M&O", value="tab1",),
                dcc.Tab(label="Upgrade M&O", value="tab2", disabled=True),
            ],
        ),
        # Content
        html.Div(id="tab-content", className="content"),
    ],
)


@app.callback(
    Output("tab-content", "children"), [Input("mou-dash-tabs", "value")]
)  # type: ignore
def render_content(tab: str) -> html.Div:
    """Create HTML for tab."""
    layouts = {"tab1": i3_mno.layout}

    return layouts[tab]()
