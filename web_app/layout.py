#!/usr/bin/env python3
"""MoU Dashboard application."""

import logging
from datetime import timedelta
from typing import Tuple

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore
import dash_html_components as html  # type: ignore
import visdcc  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore
from flask_login import current_user, login_user, logout_user  # type: ignore[import]

from .config import app
from .tabs import wbs_generic_layout
from .utils import dash_utils as du
from .utils.login import User


def layout() -> None:
    """Serve the layout to the app."""
    app.title = "MoU Dashboard"

    # Layout
    app.layout = html.Div(
        children=[
            visdcc.Run_js("refresh-for-snapshot-change"),  # pylint: disable=E1101
            visdcc.Run_js("refresh-for-login-logout"),  # pylint: disable=E1101
            #
            # Location Triggers (To Refresh Page)
            dcc.Location(id="url-1", refresh=True),
            dcc.Location(id="url-2", refresh=True),
            #
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
                            html.Label(
                                "board", className="dashboard-title board-title"
                            ),
                        ],
                    ),
                    dbc.Row(
                        className="login-container",
                        children=[
                            html.Div(id="logged-in-user", className="user",),
                            html.Div(
                                id="login-div",
                                children=dbc.Button(
                                    "log in",
                                    id="login-launch",
                                    color=du.Color.LINK,
                                    size="lg",
                                ),
                                hidden=False,
                            ),
                            html.Div(
                                id="logout-div",
                                children=dbc.Button(
                                    "log out",
                                    id="logout-launch",
                                    color=du.Color.LINK,
                                    size="lg",
                                ),
                                hidden=True,
                            ),
                        ],
                    ),
                ],
            ),
            #
            # Tabs
            dcc.Tabs(
                id="wbs-l1",
                value="mo",
                persistence=True,
                children=[
                    dcc.Tab(label="IceCube M&O", value="mo"),
                    dcc.Tab(label="IceCube Upgrade", value="upgrade"),
                ],
            ),
            #
            # Content
            html.Div(
                id="tab-content",
                className="content",
                children=wbs_generic_layout.layout(),
            ),
            #
            # Footer
            html.Div(className="footer"),
            #
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
                                color=du.Color.INFO,
                                outline=True,
                                style={"margin-top": "1rem"},
                            ),
                            dbc.Alert(
                                "Incorrect email or password",
                                id="login-bad-message",
                                color=du.Color.DANGER,
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
    Output("wbs-view-live-btn", "n_clicks"),
    [Input("wbs-l1", "value")],
    prevent_initial_call=True,
)  # type: ignore
def prep_for_tab_change(wbs_l1: str) -> int:
    """Prepare for a new tab: view the live table.

    Tab value is persisted in 'Tabs' between refreshes.
    """
    logging.warning(f"'{du.triggered_id()}' -> prep_for_tab_change()")
    logging.warning(f"tab clicked: {wbs_l1=}")
    return 0


def _logged_in_return(
    refresh: bool = True,
) -> Tuple[bool, bool, bool, bool, str, str, str]:
    if current_user.is_admin:
        user_label = f"{current_user.name} (Admin)"
    else:
        user_label = f"{current_user.name} ({current_user.institution})"

    if refresh:
        return False, False, True, False, user_label, "", "location.reload();"
    return False, False, True, False, user_label, "", ""


def _logged_out_return(
    refresh: bool = True,
) -> Tuple[bool, bool, bool, bool, str, str, str]:

    if refresh:
        return False, False, False, True, "", "", "location.reload();"
    return False, False, False, True, "", "", ""


@app.callback(  # type: ignore[misc]
    [
        Output("login-modal", "is_open"),
        Output("login-bad-message", "is_open"),
        Output("login-div", "hidden"),
        Output("logout-div", "hidden"),
        Output("logged-in-user", "children"),
        Output("login-password", "value"),
        Output("refresh-for-login-logout", "run"),
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
) -> Tuple[bool, bool, bool, bool, str, str, str]:
    """Log the institution leader in/out."""
    logging.warning(f"'{du.triggered_id()}' -> login()")

    open_login_modal = (True, False, False, True, "", "", "")
    bad_login = (True, True, False, True, "", "", "")

    if du.triggered_id() == "login-launch":
        assert not current_user.is_authenticated
        return open_login_modal

    if du.triggered_id() == "logout-launch":
        logout_user()
        assert not current_user.is_authenticated
        return _logged_out_return()

    if du.triggered_id() in ["login-button", "login-password"]:
        assert not current_user.is_authenticated
        if user := User.login(email, pwd):
            login_user(user, duration=timedelta(days=50))
            return _logged_in_return()
        # bad log-in
        return bad_login

    if du.triggered_id() == "":
        if current_user.is_authenticated:
            logging.warning(f"User already logged in {current_user}.")
            return _logged_in_return(refresh=False)
        # Initial Call w/o Stored Login
        logging.warning("User not already logged in.")
        return _logged_out_return(refresh=False)

    raise Exception(f"Unaccounted for trigger: {du.triggered_id()}")
