"""Layout root and high-level callbacks."""

import logging
from typing import Tuple

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore
import dash_html_components as html  # type: ignore
import visdcc  # type: ignore[import]
from dash import no_update  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore

from .config import AUTO_RELOAD_MINS, REDIRECT_WBS, app
from .contents import wbs_generic_layout
from .networking.connections import CurrentUser
from .utils import dash_utils as du
from .utils import utils


def layout() -> None:
    """Serve the layout to `app`."""
    app.title = "MoU Dashboard"

    # Layout
    app.layout = html.Div(
        children=[
            dcc.Interval(
                id="interval", interval=AUTO_RELOAD_MINS * 60 * 1000  # milliseconds
            ),
            #
            # To change URLs without necessarily refreshing
            dcc.Location(id="url"),  # duplicates will auto-sync values w/o triggering
            dcc.Location(id="url-user-inst-redirect"),
            dcc.Location(id="url-404-redirect"),
            #
            # JS calls for refreshing page
            visdcc.Run_js("refresh-for-snapshot-make"),  # pylint: disable=E1101
            visdcc.Run_js("refresh-for-override-success"),  # pylint: disable=E1101
            visdcc.Run_js("refresh-for-snapshot-change"),  # pylint: disable=E1101
            visdcc.Run_js("refresh-for-interval"),  # pylint: disable=E1101
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
                                className="hover-bold",
                            ),
                            dbc.NavLink(
                                id="nav-link-upgrade",
                                children="IceCube Upgrade",
                                href="/upgrade",
                                external_link=True,
                                className="hover-bold",
                            ),
                            html.Div(
                                id="nav-seperator",
                                children="■",
                                className="nav-seperator",
                            ),
                            html.Div(id="logged-in-user", className="user"),
                            html.A(
                                "Log Out",
                                className="log-inout hover-bold",
                                href="/logout",
                            ),
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
            html.Div(
                className="footer",
                children=html.Div(
                    f"Web Server Started: {utils.get_human_now()}",
                    className="footer-version",
                ),
            ),
        ],
    )


@app.callback(  # type: ignore[misc]
    Output("refresh-for-interval", "run"),
    Input("interval", "n_intervals"),  # dummy input
    prevent_initial_call=True,
)
def interval(_: int) -> str:
    """Automatically refresh/reload page on interval.

    This will help re-check for login credentials in case of an expired
    session cookie. The user will remain on the same page, unless they
    need to log in again.
    """
    logging.critical(
        f"'{du.triggered()}' -> interval() {AUTO_RELOAD_MINS=} {CurrentUser.get_summary()=}"
    )
    return du.RELOAD


@app.callback(  # type: ignore[misc]
    [
        Output("url-404-redirect", "pathname"),
        Output("tab-content", "hidden"),  # update to call view_live_table()
        Output("logged-in-user", "children"),
    ],
    [Input("url-404-redirect", "refresh")],  # never triggered
    [State("url", "pathname")],
)
def main_redirect(_: bool, s_urlpath: str) -> Tuple[str, bool, str]:
    """Redirect the url for any reason."""
    logging.critical(
        f"'{du.triggered()}' -> main_redirect() {CurrentUser.get_summary()=}"
    )

    # is the user logged-in?
    if not CurrentUser.is_loggedin():
        return "login", True, ""

    # does the user have permissions?
    if not CurrentUser.is_loggedin_with_permissions():
        return "invalid-permissions", True, ""

    if CurrentUser.is_admin():
        user_label = f"{CurrentUser.get_username()} (Admin)"
    else:
        user_label = CurrentUser.get_username()

    # is this a correct institution?
    if du.user_viewing_wrong_inst(s_urlpath):
        logging.error(f"User viewing wrong mou {s_urlpath=}. Redirecting...")
        if du.root_is_not_wbs(s_urlpath):
            root = REDIRECT_WBS
        else:
            root = du.get_wbs_l1(s_urlpath)
        # redirect
        if CurrentUser.is_admin():
            return root, False, user_label
        else:
            return f"{root}/{CurrentUser.get_institutions()[0]}", False, user_label

    # is this a known page?
    if du.root_is_not_wbs(s_urlpath):
        logging.error(f"User viewing {s_urlpath=}. Redirecting to '{REDIRECT_WBS}'...")
        return REDIRECT_WBS, False, user_label

    return no_update, False, user_label


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


@app.callback(  # type: ignore[misc]
    [
        Output("mou-title", "children"),
        Output("nav-link-mo", "active"),
        Output("nav-link-upgrade", "active"),
    ],
    Input("mou-title", "hidden"),  # dummy input
    [State("url", "pathname")],
)
def load_nav_title(_: bool, s_urlpath: str) -> Tuple[str, bool, bool]:
    """Load the title for the current mou/wbs-l1."""
    wbs_l1 = du.get_wbs_l1(s_urlpath)

    titles = {"mo": "IceCube M&O", "upgrade": "IceCube Upgrade"}
    title = f"– {titles.get(wbs_l1, '')}"  # that's an en-dash

    return title, wbs_l1 == "mo", wbs_l1 == "upgrade"
