#!/usr/bin/env python3
"""MoU Dashboard application."""

import logging
from datetime import timedelta
from typing import Final, Tuple

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
from .utils import login, types

LOG_IN: Final[str] = "Log In"
LOG_OUT: Final[str] = "Log Out"


def layout() -> None:
    """Serve the layout to `app`."""
    app.title = "MoU Dashboard"

    # Layout
    app.layout = html.Div(
        children=[
            dcc.Location(id="url"),  # , pathname="mo", refresh=False),
            #
            # JS calls for refreshing page
            visdcc.Run_js("refresh-for-login-logout"),  # pylint: disable=E1101
            visdcc.Run_js("refresh-for-snapshot-make"),  # pylint: disable=E1101
            visdcc.Run_js("refresh-for-override-success"),  # pylint: disable=E1101
            visdcc.Run_js("refresh-for-snapshot-change"),  # pylint: disable=E1101
            visdcc.Run_js("refresh-for-institution-change"),  # pylint: disable=E1101
            #
            # Logo, Tabs, & Login
            dbc.Navbar(
                sticky="top",
                expand="lg",
                children=[
                    # Logo
                    dbc.Row(
                        className="logo-container",
                        children=[
                            html.Label("MoU", className="logo-mou"),
                            html.Label("Dash", className="logo-dashboard logo-dash"),
                            html.Label("board", className="logo-dashboard logo-board"),
                            html.Label(
                                "– IceCube MoUs",
                                id="mou-title",
                                className="logo-mou-current",
                            ),
                        ],
                    ),
                    dbc.NavbarToggler(id="navbar-toggler"),
                    # Items
                    dbc.Collapse(
                        id="navbar-collapse",
                        className="navbar-uncollapsed",
                        navbar=True,
                        children=[
                            dbc.NavLink(
                                id="nav-link-mo",
                                children="IceCube M&O",
                                href="/mo",
                                external_link=True,
                            ),
                            dbc.NavLink(
                                id="nav-link-upgrade",
                                children="IceCube Upgrade",
                                href="/upgrade",
                                external_link=True,
                            ),
                            html.Div(
                                id="nav-seperator",
                                children="■",
                                className="nav-seperator",
                            ),
                            html.Div(id="logged-in-user", className="user"),
                            html.Div(id="log-inout-launch", className="log-inout"),
                        ],
                    ),
                ],
                color="black",
                dark=True,
            ),
            #
            # Content
            html.Div(
                id="tab-content",
                className="content",
                children=wbs_generic_layout.layout(),
                hidden=False,
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
                                placeholder="IceCube Username",
                                pattern=r"[~!]?[a-zA-Z0-9]*",
                                persistence=True,
                                persistence_type="memory",
                                type="text",
                                style={"width": "50%"},
                            ),
                            # Password
                            dcc.Input(
                                id="login-password",
                                placeholder="Password",
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


@app.callback(  # type: ignore[misc]
    [
        Output("navbar-collapse", "is_open"),
        Output("navbar-collapse", "className"),
        Output("nav-seperator", "hidden"),
    ],
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n_clicks: int, is_open: bool) -> Tuple[bool, str, bool]:
    """Toggle the navbar collapse on small screens.

    https://dash-bootstrap-components.opensource.faculty.ai/docs/components/navbar/#
    """
    if n_clicks:
        return not is_open, "", not is_open
    return is_open, "navbar-uncollapsed", is_open


@app.callback(
    Output("tab-content", "hidden"),  # update to call view_live_table()
    [Input("tab-content", "className")],  # never triggered
)  # type: ignore
def show_tab_content(_: str) -> bool:
    """Show/Hide tab content."""
    assert not du.triggered_id()

    return not current_user.is_authenticated


@app.callback(
    [
        Output("mou-title", "children"),
        Output("nav-link-mo", "active"),
        Output("nav-link-upgrade", "active"),
    ],
    Input("mou-title", "hidden"),  # dummy input
    [State("url", "pathname")],
)  # type: ignore
def load_mou(_: bool, s_urlpath: str) -> Tuple[str, bool, bool]:
    """Load the title for the current mou/wbs-l1."""
    wbs_l1 = du.get_wbs_l1(s_urlpath)

    titles = {"mo": "IceCube M&O", "upgrade": "IceCube Upgrade"}
    title = f"– {titles.get(wbs_l1, '')}"  # that's an en-dash

    return title, wbs_l1 == "mo", wbs_l1 == "upgrade"


def _logged_in_return(
    reload: bool = True,
) -> Tuple[str, bool, bool, str, str, str, bool, str]:
    if current_user.is_admin:
        user_label = f"{current_user.name} (Admin)"
    else:
        user_label = f"{current_user.name}"

    logging.error(f"{current_user=}")

    if reload:
        return du.RELOAD, False, False, "", LOG_OUT, user_label, False, ""
    return no_update, False, False, "", LOG_OUT, user_label, False, ""


def _logged_out_return(
    reload: bool = True,
) -> Tuple[str, bool, bool, str, str, str, bool, str]:

    if reload:
        return du.RELOAD, False, False, "", LOG_IN, "", True, ""
    return no_update, False, False, "", LOG_IN, "", True, ""


@app.callback(  # type: ignore[misc]
    [
        Output("refresh-for-login-logout", "run"),
        Output("login-modal", "is_open"),
        Output("login-bad-message", "is_open"),
        Output("login-bad-message", "children"),
        Output("log-inout-launch", "children"),
        Output("logged-in-user", "children"),
        Output("logged-in-user", "hidden"),
        Output("login-password", "value"),
    ],
    [
        Input("login-button", "n_clicks"),  # user-only
        Input("log-inout-launch", "n_clicks"),  # user-only
        Input("login-password", "n_submit"),  # user-only
    ],
    [
        State("login-username", "value"),
        State("login-password", "value"),
        State("login-manual-institution", "value"),  # TODO: remove when keycloak
        State("log-inout-launch", "children"),
    ],
)  # pylint: disable=R0911
def login_callback(
    _: int,
    __: int,
    ___: int,
    username: str,
    pwd: str,
    inst: types.DashVal,
    s_log_inout: str,
) -> Tuple[str, bool, bool, str, str, str, bool, str]:
    """Log the institution leader in/out."""
    logging.warning(f"'{du.triggered_id()}' -> login_callback()")

    if du.triggered_id() == "log-inout-launch":
        if s_log_inout == LOG_IN:  # pylint: disable=R1705
            assert not current_user.is_authenticated
            return no_update, True, False, "", LOG_IN, "", True, ""
        elif s_log_inout == LOG_OUT:
            logout_user()
            assert not current_user.is_authenticated
            return _logged_out_return()
        else:
            raise Exception(f"Undefined Log-In/Out Value: {s_log_inout=}")

    if du.triggered_id() in ["login-button", "login-password"]:
        assert not current_user.is_authenticated
        try:
            # TODO: remove inst when keycloak
            user = login.User.try_login(username, pwd, inst)
            # all good now
            login_user(user, duration=timedelta(days=50))
            return _logged_in_return()
        # bad log-in
        except login.InvalidUsernameException:
            msg = "Username not found"
            return no_update, True, True, msg, LOG_IN, "", True, ""
        except login.InvalidPasswordException:
            msg = "Wrong password"
            return no_update, True, True, msg, LOG_IN, "", True, ""
        except login.NoUserInstitutionException:
            msg = "An institution must be selected"
            return no_update, True, True, msg, LOG_IN, "", True, ""

    if du.triggered_id() == "":  # aka on page-load
        if current_user.is_authenticated:
            logging.warning(f"User already logged in {current_user}.")
            return _logged_in_return(reload=False)
        # Initial Call w/o Stored Login
        logging.warning("User not already logged in.")
        return _logged_out_return(reload=False)

    raise Exception(f"Unaccounted for trigger: {du.triggered_id()}")
