#!/usr/bin/env python3
"""MoU Dashboard application."""

import logging
from datetime import timedelta
from typing import Tuple

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore
import dash_html_components as html  # type: ignore
import visdcc  # type: ignore[import]
from dash import no_update  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore
from flask_login import current_user, login_user, logout_user  # type: ignore[import]

from .config import app
from .data_source import table_config as tc
from .tabs import wbs_generic_layout
from .utils import dash_utils as du
from .utils import types
from .utils.login import InvalidLoginException, User


def layout() -> None:
    """Serve the layout to `app`."""
    app.title = "MoU Dashboard"

    # Layout
    app.layout = html.Div(
        children=[
            #
            # JS calls for refreshing page
            visdcc.Run_js("refresh-for-snapshot-make"),  # pylint: disable=E1101
            visdcc.Run_js("refresh-for-override-success"),  # pylint: disable=E1101
            visdcc.Run_js("refresh-for-snapshot-change"),  # pylint: disable=E1101
            visdcc.Run_js("refresh-for-institution-change"),  # pylint: disable=E1101
            #
            # Logo & Login
            dbc.Row(
                justify="start",
                className="top-container",
                children=[
                    #
                    # Logo
                    dbc.Row(
                        className="logo-container",
                        children=[
                            html.Label("MoU", className="logo-mou"),
                            html.Label("Dash", className="logo-dashboard logo-dash"),
                            html.Label("board", className="logo-dashboard logo-board"),
                        ],
                    ),
                    #
                    # Login
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
                id="wbs-current-l1",
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
                            # username
                            dcc.Input(
                                id="login-username",
                                placeholder="username",
                                persistence=True,
                                persistence_type="memory",
                                type="text",
                                style={"width": "50%"},
                            ),
                            # Password
                            dcc.Input(
                                id="login-password",
                                placeholder="password",
                                type="password",
                                style={"width": "50%"},
                            ),
                            # User-Institution Dropdown
                            # TODO: remove when keycloak
                            dcc.Dropdown(
                                id="login-manual-institution",
                                style={"margin-top": "1rem"},
                                placeholder="Your Institution",
                                options=[
                                    {"label": f"{abbrev} ({name})", "value": abbrev}
                                    for name, abbrev in tc.TableConfigParser(
                                        "mo"
                                    ).get_institutions_w_abbrevs()
                                ],
                            ),
                            # Log-in Button
                            dbc.Button(
                                "Log In",
                                id="login-button",
                                n_clicks=0,
                                color=du.Color.INFO,
                                outline=True,
                                style={"margin-top": "1rem"},
                            ),
                            # Alert
                            dbc.Alert(
                                # TODO: remove 'institution' when keycloak
                                "Incorrect username, password, or institution",
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
    Output("wbs-view-live-btn", "n_clicks"),  # update to call view_live_table()
    [Input("wbs-current-l1", "value")],  # user-only
    prevent_initial_call=True,
)  # type: ignore
def pick_tab(wbs_l1: str) -> int:
    """Prepare for a new tab: view the live table.

    Tab value is persisted in 'Tabs' between refreshes.
    """
    logging.warning(f"'{du.triggered_id()}' -> pick_tab()")
    logging.warning(f"tab clicked: {wbs_l1=}")
    return 0


def _logged_in_return(
    select_institution: bool = True,
) -> Tuple[bool, bool, bool, bool, str, str, str]:
    if current_user.is_admin:
        user_label = f"{current_user.name} (Admin)"
    else:
        user_label = f"{current_user.name}"

    if select_institution:
        assert current_user.institution or current_user.is_admin
        return False, False, True, False, user_label, "", current_user.institution
    return False, False, True, False, user_label, "", no_update


def _logged_out_return(
    select_institution: bool = True,
) -> Tuple[bool, bool, bool, bool, str, str, str]:

    if select_institution:
        return False, False, False, True, "", "", ""
    return False, False, False, True, "", "", no_update


@app.callback(  # type: ignore[misc]
    [
        Output("login-modal", "is_open"),
        Output("login-bad-message", "is_open"),
        Output("login-div", "hidden"),
        Output("logout-div", "hidden"),
        Output("logged-in-user", "children"),
        Output("login-password", "value"),
        Output("wbs-login-institution", "data"),  # update to call pick_institution()
    ],
    [
        Input("login-button", "n_clicks"),  # user-only
        Input("login-launch", "n_clicks"),  # user-only
        Input("logout-launch", "n_clicks"),  # user-only
        Input("login-password", "n_submit"),  # user-only
    ],
    [
        State("login-username", "value"),
        State("login-password", "value"),
        State("login-manual-institution", "value"),  # TODO: remove when keycloak
    ],
)
def login(
    _: int, __: int, ___: int, ____: int, username: str, pwd: str, inst: types.DashVal
) -> Tuple[bool, bool, bool, bool, str, str, types.DashVal]:
    """Log the institution leader in/out."""
    logging.warning(f"'{du.triggered_id()}' -> login()")

    open_login_modal = (True, False, False, True, "", "", no_update)
    bad_login = (True, True, False, True, "", "", no_update)

    if du.triggered_id() == "login-launch":
        assert not current_user.is_authenticated
        return open_login_modal

    if du.triggered_id() == "logout-launch":
        logout_user()
        assert not current_user.is_authenticated
        return _logged_out_return()

    if du.triggered_id() in ["login-button", "login-password"]:
        assert not current_user.is_authenticated
        inst = inst if isinstance(inst, str) else ""  # TODO: remove when keycloak
        try:
            user = User.try_login(username, pwd, inst)
            login_user(user, duration=timedelta(days=50))
            return _logged_in_return()
        # bad log-in
        except InvalidLoginException:
            return bad_login

    if du.triggered_id() == "":  # aka on page-load
        if current_user.is_authenticated:
            logging.warning(f"User already logged in {current_user}.")
            return _logged_in_return(select_institution=False)
        # Initial Call w/o Stored Login
        logging.warning("User not already logged in.")
        return _logged_out_return(select_institution=False)

    raise Exception(f"Unaccounted for trigger: {du.triggered_id()}")
