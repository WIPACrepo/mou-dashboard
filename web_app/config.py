"""Config file."""

import dataclasses as dc
import logging
from typing import Final
from urllib.parse import urljoin

import dash  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import flask
import werkzeug
from cachelib import SimpleCache
from flask_oidc import OpenIDConnect  # type: ignore[import]
from flask_session import Session
from wipac_dev_tools import from_environment_as_dataclass

AUTO_RELOAD_MINS = 15  # how often to auto-reload the page
MAX_CACHE_MINS = 5  # how often to expire a cache result

REDIRECT_WBS = "mo"  # which mou to go to by default when ambiguously redirecting


# --------------------------------------------------------------------------------------
# configure config_vars


@dc.dataclass(frozen=True)
class EnvConfig:
    """For storing environment variables, typed."""

    # pylint:disable=invalid-name
    REST_SERVER_URL: str = "http://localhost:8080"
    TOKEN_SERVER_URL: str = "http://localhost:8888"
    WEB_SERVER_HOST: str = "localhost"
    WEB_SERVER_PORT: int = 8050
    AUTH_PREFIX: str = "mou"
    TOKEN_REQUEST_URL: str = dc.field(init=False)
    TOKEN: str = ""
    FLASK_SECRET: str = "super-secret-flask-key"
    OIDC_CLIENT_SECRETS: str = "client_secrets.json"
    OVERWRITE_REDIRECT_URI: str = ""
    DEBUG: bool = False
    DEBUG_AS_PI: list[str] = dc.field(default_factory=list)
    LOG_REST_CALLS: bool = True

    CI_TEST: bool = False

    def __post_init__(self) -> None:
        # since our instance is frozen, we need to use `__setattr__`
        object.__setattr__(
            self,
            "TOKEN_REQUEST_URL",
            urljoin(self.TOKEN_SERVER_URL, f"token?scope={self.AUTH_PREFIX}:admin"),
        )


ENV: Final = from_environment_as_dataclass(EnvConfig)


def log_config_vars() -> None:
    """Log the global configuration variables, key-value."""
    for field in dc.fields(ENV):
        logging.info(
            f"{field.name}\t{getattr(ENV, field.name)}\t({type(getattr(ENV, field.name)).__name__})"
        )


# --------------------------------------------------------------------------------------
# Set-up Dash server

app = dash.Dash(
    __name__,
    server=flask.Flask(__name__),
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://codepen.io/chriddyp/pen/bWLwgP.css",
        "https://fonts.googleapis.com/css2?family=Syncopate",
        "https://fonts.googleapis.com/css2?family=Sarpanch",
        "https://fonts.googleapis.com/css2?family=Kanit:wght@200",
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.2/css/all.min.css",
    ],
)

# config
server = app.server
app.config.suppress_callback_exceptions = True
server.config.update(SECRET_KEY=ENV.FLASK_SECRET)

# Store sessions server-side: the OIDC token + userinfo (needed for group-based
# auth) don't fit in a client-side cookie (browsers cap cookies at ~4096 bytes).
server.config.update(SESSION_TYPE="cachelib", SESSION_CACHELIB=SimpleCache())
Session(server)


# --------------------------------------------------------------------------------------
# configure keycloak login

# from https://gist.github.com/thomasdarimont/145dc9aa857b831ff2eff221b79d179a
server.config.update(
    {
        # "TESTING": True,
        # "DEBUG": True,
        "OIDC_CLIENT_SECRETS": ENV.OIDC_CLIENT_SECRETS,
        # "OIDC_ID_TOKEN_COOKIE_SECURE": False, # default: True
        # "OIDC_REQUIRE_VERIFIED_EMAIL": True,  # default: False
        # "OIDC_USER_INFO_ENABLED": True, # default: True
        # "OIDC_OPENID_REALM": "flask-demo", # default: None
        # "OIDC_SCOPES": ["openid", "email", "profile"], # default: ["openid", "email"]
        # "OIDC_INTROSPECTION_AUTH_METHOD": "client_secret_post",  # default: client_secret_post
        "OIDC_OVERWRITE_REDIRECT_URI": ENV.OVERWRITE_REDIRECT_URI,
    }
)
oidc = OpenIDConnect(server)  # grabs "OIDC_CLIENT_SECRETS"/ENV.OIDC_CLIENT_SECRETS


@server.after_request  # type: ignore[misc]
def _log_auth_redirects(
    response: werkzeug.wrappers.response.Response,  # type: ignore[name-defined]
) -> werkzeug.wrappers.response.Response:  # type: ignore[name-defined]
    """Log every server-side (HTTP) redirect, to help diagnose login/logout loops.

    Dash's own page navigation (e.g. '/' -> '/mo') happens client-side via JS and
    never shows up here. Only real HTTP redirects do: the OIDC login/authorize/
    logout hops -- notably including flask-oidc's *forced* logout when it can't
    refresh an access token, which fires no signal of its own and would
    otherwise be invisible.
    """
    if 300 <= response.status_code < 400:
        logging.info(
            f"AUTH-REDIRECT {flask.request.method} {flask.request.path} -> "
            f"{response.status_code} Location={response.location!r} "
            f"oidc_token={'present' if flask.session.get('oidc_auth_token') else 'absent'}"
        )
    return response


@server.route("/invalid-permissions")  # type: ignore[misc]
def invalid_permissions() -> str | werkzeug.wrappers.response.Response:  # type: ignore[name-defined]
    """Redirected to tell the user they can't do anything other than logout."""
    logging.critical("/invalid-permissions")
    return (
        'You don\'t have valid permissions to edit MOUs. <a href="/logout">Logout</a>'
    )
