"""Config file."""

import logging
from typing import TypedDict
from urllib.parse import urljoin

import dash  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import flask  # type: ignore
from flask_caching import Cache  # type: ignore[import]
from flask_oidc import OpenIDConnect  # type: ignore[import]

# local imports
from rest_tools.server.config import from_environment  # type: ignore[import]

# --------------------------------------------------------------------------------------
# configure config_vars


class ConfigVarsTypedDict(TypedDict, total=False):
    """Global configuration-variable types."""

    REST_SERVER_URL: str
    TOKEN_SERVER_URL: str
    WEB_SERVER_HOST: str
    WEB_SERVER_PORT: int
    AUTH_PREFIX: str
    TOKEN_REQUEST_URL: str
    TOKEN: str
    NO_USER_AUTH_REQ: bool
    FLASK_SECRET: str


def get_config_vars() -> ConfigVarsTypedDict:
    """Get the global configuration variables."""
    config_vars: ConfigVarsTypedDict = from_environment(
        {
            "REST_SERVER_URL": "http://localhost:8080",
            "TOKEN_SERVER_URL": "http://localhost:8888",
            "WEB_SERVER_HOST": "localhost",
            "WEB_SERVER_PORT": 8050,
            "AUTH_PREFIX": "mou",
            "TOKEN": "",
            "FLASK_SECRET": "super-secret-flask-key",
        }
    )

    config_vars["TOKEN_REQUEST_URL"] = urljoin(
        config_vars["TOKEN_SERVER_URL"],
        f"token?scope={config_vars['AUTH_PREFIX']}:admin",
    )

    return config_vars


def log_config_vars() -> None:
    """Log the global configuration variables, key-value."""
    for key, val in get_config_vars().items():
        logging.info(f"{key}\t{val}\t({type(val).__name__})")


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
        "https://fonts.googleapis.com/css2?family=Kanit:ital,wght@1,200",
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css",
    ],
)

# config
server = app.server
app.config.suppress_callback_exceptions = True
server.config.update(SECRET_KEY=get_config_vars()["FLASK_SECRET"])
cache = Cache(app.server, config={"CACHE_TYPE": "simple"})


# --------------------------------------------------------------------------------------
# configure keycloak login


server.config.update(
    {
        # "TESTING": True,
        # "DEBUG": True,
        "OIDC_CLIENT_SECRETS": "client_secrets.json",
        "OIDC_ID_TOKEN_COOKIE_SECURE": False,
        "OIDC_REQUIRE_VERIFIED_EMAIL": False,
        "OIDC_USER_INFO_ENABLED": True,
        "OIDC_OPENID_REALM": "flask-demo",
        "OIDC_SCOPES": ["openid", "email", "profile"],
        "OIDC_INTROSPECTION_AUTH_METHOD": "client_secret_post",
    }
)
oidc = OpenIDConnect(server)


@server.route("/login")  # type: ignore[misc]
@oidc.require_login  # type: ignore[misc]
def login() -> flask.Response:
    """On successful login, redirect to index."""
    logging.critical("/login")
    return flask.redirect("/")


@server.route("/logout")  # type: ignore[misc]
def logout() -> flask.Response:
    """Performs local logout by removing the session cookie."""
    logging.critical("/logout")
    oidc.logout()
    return 'Hi, you have been logged out! <a href="/">Login</a>'


@server.route("/invalid-permissions")  # type: ignore[misc]
def invalid_permissions() -> flask.Response:
    """Redirected to tell the user they can't do anything other than logout."""
    logging.critical("/invalid-permissions")
    return 'You don\'t have permissions to edit MoUs. <a href="/logout">Logout</a>'
