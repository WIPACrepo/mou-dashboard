#!/usr/bin/env python3
"""MoU Dashboard application."""

from typing import Tuple

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore
import dash_html_components as html  # type: ignore
from dash.dependencies import Input, Output, State  # type: ignore
from flask_login import current_user, login_user, logout_user  # type: ignore[import]

from .config import app, User
from .tabs import i3
from .utils.dash_utils import Color, triggered_id

# Layout
app.layout = html.Div(
    className="background",
    children=[
        # Title
        dbc.Row(
            justify="start",
            style={"display": "flex"},
            children=[
                dbc.Row(
                    className="title-container",
                    children=[
                        html.Label("MoU", className="mou-title"),
                        html.Label("Dash", className="dashboard-title dash-title"),
                        html.Label("board", className="dashboard-title board-title"),
                    ],
                ),
                dbc.Row(
                    className="login-container",
                    children=[
                        html.Div(
                            id="tab-1-logged-in-user",
                            className="caps",
                            style={
                                "fontSize": 15,
                                "font-style": "italic",
                                "padding-top": "0.9rem",
                            },
                        ),
                        html.Div(
                            id="login-div",
                            children=dbc.Button(
                                "log in", id="login-launch", color=Color.LINK, size="lg"
                            ),
                            hidden=False,
                        ),
                        html.Div(
                            id="logout-div",
                            children=dbc.Button(
                                "log out",
                                id="logout-launch",
                                color=Color.LINK,
                                size="lg",
                            ),
                            hidden=True,
                        ),
                    ],
                ),
            ],
        ),
        # Tabs
        dcc.Tabs(
            id="mou-dash-tabs",
            value="tab1",
            children=[
                dcc.Tab(label="IceCube M&O", value="tab1",),
                dcc.Tab(label="IceCube Upgrade", value="tab2", disabled=True),
            ],
        ),
        # Content
        html.Div(id="tab-content", className="content"),
        dbc.Modal(
            id="login-modal",
            size="md",
            is_open=True,
            children=[
                dbc.ModalBody(
                    children=[
                        html.Div(
                            "Institution Leader Login",
                            className="caps",
                            style={"margin-bottom": "2rem"},
                        ),
                        dcc.Input(
                            id="login-username",
                            placeholder="username",
                            type="text",
                            style={"width": "50%"},
                        ),
                        dcc.Input(
                            id="login-password",
                            placeholder="password",
                            type="password",
                            style={"width": "50%"},
                        ),
                        dbc.Button(
                            "Log In",
                            id="login-button",
                            n_clicks=0,
                            color=Color.INFO,
                            outline=True,
                            style={"margin-top": "1rem"},
                        ),
                        dbc.Alert(
                            "Incorrect username or password",
                            id="output-state",
                            color=Color.DANGER,
                            style={"margin-top": "2rem"},
                            is_open=False,
                        ),
                    ],
                ),
            ],
        ),
    ],
)


@app.callback(
    Output("tab-content", "children"), [Input("mou-dash-tabs", "value")]
)  # type: ignore
def render_content(tab: str) -> html.Div:
    """Create HTML for tab."""
    layouts = {"tab1": i3.layout}

    return layouts[tab]()


@app.callback(  # type: ignore[misc]
    [
        Output("output-state", "is_open"),
        Output("login-modal", "is_open"),
        Output("login-div", "hidden"),
        Output("logout-div", "hidden"),
        Output("tab-1-logged-in-user", "children"),
    ],
    [
        Input("login-button", "n_clicks"),
        Input("login-launch", "n_clicks"),
        Input("logout-launch", "n_clicks"),
        Input("login-password", "n_submit"),
    ],
    [State("login-username", "value"), State("login-password", "value")],
    prevent_initial_call=True,
)
def login(
    _: int, __: int, ___: int, ____: int, uname: str, pwd: str
) -> Tuple[bool, bool, bool, bool, str]:
    """Log the institution leader in/out."""
    if triggered_id() == "login-launch":
        logout_user()
        return False, True, False, True, ""

    if triggered_id() == "logout-launch":
        return False, False, False, True, ""

    user = User.login(uname, pwd)
    if user:
        login_user(user)
        user_label = f"{current_user.username} ({current_user.institution})"
        return False, False, True, False, user_label
    # fall-through
    return True, True, False, True, ""
