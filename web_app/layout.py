"""Layout root and high-level callbacks."""

import logging

import dash_bootstrap_components as dbc  # type: ignore[import]
import visdcc  # type: ignore[import]
from dash import dcc, html, no_update  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore

from .config import AUTO_RELOAD_MINS, ENV, REDIRECT_WBS, app
from .contents import wbs_generic_layout
from .data_source.connections import CurrentUser
from .utils import dash_utils as du
from .utils import utils


def layout() -> None:
    """Serve the layout to `app`."""
    app.title = "MOU Dashboard"
    if ENV.CI_TEST:
        app.title = "Test -- MOU Dashboard"

    # Layout
    app.layout = html.Div(
        children=[
            dcc.Interval(
                id="interval-page-reload",
                interval=AUTO_RELOAD_MINS * 60 * 1000,  # milliseconds
            ),
            #
            # To change URLs without necessarily refreshing
            dcc.Location(id="url"),  # duplicates will auto-sync values w/o triggering
            dcc.Location(id="url-user-inst-redirect"),
            dcc.Location(id="url-404-redirect"),
            #
            # JS calls for reloading page
            visdcc.Run_js("reload-for-snapshot-make"),  # pylint: disable=E1101
            visdcc.Run_js("reload-for-override-success"),  # pylint: disable=E1101
            visdcc.Run_js("reload-for-snapshot-change"),  # pylint: disable=E1101
            visdcc.Run_js("reload-for-interval"),  # pylint: disable=E1101
            visdcc.Run_js("reload-for-retouchstone"),  # pylint: disable=E1101
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
                            dbc.Col(
                                html.Img(
                                    id="mou-logo",
                                    src="/assets/mou_dash_mo.png",
                                    alt="MOU Dashboard",
                                    # width="600em",
                                    height="30em",
                                ),
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
                            html.A(
                                "User Guide PDF",
                                download="MOU_Dashboard_Getting_Started.pdf",
                                href="/assets/MOU_Dashboard_Getting_Started.pdf",
                                className="hover-bold nav-link",
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
    Output("reload-for-interval", "run"),
    Input("interval-page-reload", "n_intervals"),  # dummy input
    prevent_initial_call=True,
)
def interval_page_reload(_: int) -> str:
    """Automatically refresh/reload page on interval.

    This will help re-check for login credentials in case of an expired
    session cookie. The user will remain on the same page, unless they
    need to log in again.
    """
    logging.critical(
        f"'{du.triggered()}' -> interval_page_reload() {AUTO_RELOAD_MINS=} {CurrentUser.get_summary()=}"
    )
    return du.RELOAD


@app.callback(  # type: ignore[misc]
    [
        Output("url-404-redirect", "pathname"),
        Output("tab-content", "hidden"),  # update to call view_live_table()
        Output("logged-in-user", "children"),
    ],
    [Input("url-404-redirect", "refresh")],  # `refresh` is never triggered
    [State("url", "pathname")],
)
def main_redirect(_: bool, s_urlpath: str) -> tuple[str, bool, str]:
    """Redirect the url for any reason."""
    logging.critical(
        f"'{du.triggered()}' -> main_redirect() {CurrentUser.get_summary()=}"
    )

    # is the user logged-in?
    if not CurrentUser.is_loggedin():
        logging.warning("Redirecting to '/login' ...")
        return "login", True, ""

    # does the user have permissions?
    if not CurrentUser.is_loggedin_with_permissions():
        logging.warning("Redirecting to '/invalid-permissions' ...")
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
            url = root
        else:
            url = f"{root}/{CurrentUser.get_institutions()[0]}"
        logging.warning(f"Redirecting to '/{url}' ...")
        return url, False, user_label

    # is this a known page?
    if du.root_is_not_wbs(s_urlpath):
        logging.error(f"User viewing {s_urlpath=}")
        logging.warning(f"Redirecting to '/{REDIRECT_WBS}' ...")
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
def toggle_navbar_collapse(n_clicks: int, is_open: bool) -> tuple[bool, str, bool]:
    """Toggle the navbar collapse on small screens.

    https://dash-bootstrap-components.opensource.faculty.ai/docs/components/navbar/#
    """
    if n_clicks:
        return not is_open, "", not is_open
    return is_open, "navbar-uncollapsed", is_open


@app.callback(  # type: ignore[misc]
    [
        Output("mou-logo", "src"),
        Output("nav-link-mo", "active"),
        Output("nav-link-upgrade", "active"),
    ],
    Input("mou-logo", "hidden"),  # dummy input
    [State("url", "pathname")],
)
def load_nav_logo(_: bool, s_urlpath: str) -> tuple[str, bool, bool]:
    """Load the title logo for the current mou/wbs-l1."""
    wbs_l1 = du.get_wbs_l1(s_urlpath)

    logo = {
        "mo": "/assets/mou_dash_mo.png",
        "upgrade": "/assets/mou_dash_upgrade.png",
    }.get(wbs_l1, "")

    return logo, wbs_l1 == "mo", wbs_l1 == "upgrade"
