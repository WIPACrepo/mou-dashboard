#!/usr/bin/env python3
"""MoU Dashboard application."""

import logging
from datetime import timedelta
from typing import Tuple

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore
import dash_html_components as html  # type: ignore
from dash.dependencies import Input, Output, State  # type: ignore
from flask_login import current_user, login_user, logout_user  # type: ignore[import]

from .config import app
from .tabs import wbs_generic
from .utils.dash_utils import Color, triggered_id
from .utils.login import User

# Layout
app.layout = html.Div(
    # className="background",
    children=[
        # Title
        dbc.Row(
            justify="start",
            className="top-container",
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
                        html.Div(id="logged-in-user", className="user",),
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
            id="wbs-l1",
            value="mo",
            children=[
                dcc.Tab(label="IceCube M&O", value="mo",),
                dcc.Tab(label="IceCube Upgrade", value="upgrade"),
            ],
        ),
        # Content
        # TODO -- maybe add dcc.Store for tab value to persist b/n refreshes -- check on load
        html.Div(id="tab-content", className="content"),
        ###
        html.Div(className="footer"),
        ###
        # Log In Modal
        dbc.Modal(
            id="login-modal",
            size="md",
            # is_open=True,
            children=[
                dbc.ModalBody(
                    children=[
                        html.Div("Institution Leader Login", className="caps"),
                        # Email
                        dcc.Input(
                            id="login-email",
                            placeholder="email",
                            persistence=True,
                            persistence_type="memory",
                            type="email",
                            style={"width": "50%"},
                        ),
                        # Password
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
                            "Incorrect email or password",
                            id="login-bad-message",
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
    Output("tab-content", "children"), [Input("wbs-l1", "value")]
)  # type: ignore
def render_content(_: str) -> html.Div:
    """Create HTML for tab."""
    return wbs_generic.layout()


def _logged_in_return() -> Tuple[bool, bool, bool, bool, str, str]:
    if current_user.is_admin:
        user_label = f"{current_user.name} (Admin)"
    else:
        user_label = f"{current_user.name} ({current_user.institution})"
    return False, False, True, False, user_label, ""


@app.callback(  # type: ignore[misc]
    [
        Output("login-modal", "is_open"),
        Output("login-bad-message", "is_open"),
        Output("login-div", "hidden"),
        Output("logout-div", "hidden"),
        Output("logged-in-user", "children"),
        Output("login-password", "value"),
    ],
    [
        Input("login-button", "n_clicks"),
        Input("login-launch", "n_clicks"),
        Input("logout-launch", "n_clicks"),
        Input("login-password", "n_submit"),
    ],
    [State("login-email", "value"), State("login-password", "value")],
)
def login(
    _: int, __: int, ___: int, ____: int, email: str, pwd: str,
) -> Tuple[bool, bool, bool, bool, str, str]:
    """Log the institution leader in/out."""
    logged_out = (False, False, False, True, "", "")
    open_login_modal = (True, False, False, True, "", "")
    bad_login = (True, True, False, True, "", "")

    if triggered_id() == "login-launch":
        assert not current_user.is_authenticated
        return open_login_modal

    if triggered_id() == "logout-launch":
        logout_user()
        assert not current_user.is_authenticated
        return logged_out

    if triggered_id() in ["login-button", "login-password"]:
        assert not current_user.is_authenticated
        if user := User.login(email, pwd):
            login_user(user, duration=timedelta(days=50))
            return _logged_in_return()
        # bad log-in
        return bad_login

    if triggered_id() == "":
        if current_user.is_authenticated:
            logging.warning(f"User already logged in {current_user}.")
            return _logged_in_return()
        # Initial Call w/o Stored Login
        logging.warning("User not already logged in.")
        return logged_out

    raise Exception(f"Unaccounted for trigger: {triggered_id()}")
