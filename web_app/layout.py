#!/usr/bin/env python3
"""MoU Dashboard application."""

import dash_core_components as dcc  # type: ignore
import dash_html_components as html  # type: ignore
from dash.dependencies import Input, Output  # type: ignore

from .config import app
from .tabs import i3_mno
from .utils.styles import CONTENT_STYLE, TAB_SELECTED_STYLE, TAB_STYLE, TABS_STYLE

app.layout = html.Div(
    style={"padding-left": "5%", "padding-right": "5%", "backgroundColor": "#D3D7CFFF"},
    children=[
        html.Label(
            style={
                "fontSize": 55,
                "font-family": [
                    "Palatino Linotype",
                    "Book Antiqua",
                    "Palatino",
                    "serif",
                ],
                "font-weight": "550",
                "font-style": "oblique",
            },
            children="MoU Dashboard",
        ),
        html.Div(
            style={"backgroundColor": "white"},
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
                    colors={"primary": "green", "background": "#F3F3F3FF",},
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
