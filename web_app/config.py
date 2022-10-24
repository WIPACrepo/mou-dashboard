"""Config file."""

import logging
from typing import TypedDict

import dash  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import flask  # type: ignore
from flask_oidc import OpenIDConnect  # type: ignore[import]

# local imports
from rest_tools.server.config import from_environment  # type: ignore[import]

AUTO_RELOAD_MINS = 30  # how often to auto-reload the page
MAX_CACHE_MINS = 5  # how often to expire a cache result

REDIRECT_WBS = "mo"  # which mou to go to by default when ambiguously redirecting


# --------------------------------------------------------------------------------------
# configure config_vars


class ConfigVarsTypedDict(TypedDict):
    """Global configuration-variable types."""

    REST_SERVER_URL: str
    WEB_SERVER_HOST: str
    WEB_SERVER_PORT: int
    FLASK_SECRET: str
    OIDC_CLIENT_SECRETS: str
    OVERWRITE_REDIRECT_URI: str
    CI_TEST_ENV: bool


def get_config_vars() -> ConfigVarsTypedDict:
    """Get the global configuration variables."""
    config_vars: ConfigVarsTypedDict = from_environment(
        {
            "REST_SERVER_URL": "http://localhost:8080",
            "WEB_SERVER_HOST": "localhost",
            "WEB_SERVER_PORT": 8050,
            "FLASK_SECRET": "super-secret-flask-key",
            "OIDC_CLIENT_SECRETS": "client_secrets.json",
            "OVERWRITE_REDIRECT_URI": "",
            "CI_TEST_ENV": False,
        }
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


# --------------------------------------------------------------------------------------
# configure keycloak login

# from https://gist.github.com/thomasdarimont/145dc9aa857b831ff2eff221b79d179a
server.config.update(
    {
        # "TESTING": True,
        # "DEBUG": True,
        "OIDC_CLIENT_SECRETS": get_config_vars()["OIDC_CLIENT_SECRETS"],
        # "OIDC_ID_TOKEN_COOKIE_SECURE": False, # default: True
        # "OIDC_REQUIRE_VERIFIED_EMAIL": True,  # default: False
        # "OIDC_USER_INFO_ENABLED": True, # default: True
        # "OIDC_OPENID_REALM": "flask-demo", # default: None
        # "OIDC_SCOPES": ["openid", "email", "profile"], # default: ["openid", "email"]
        # "OIDC_INTROSPECTION_AUTH_METHOD": "client_secret_post",  # default: client_secret_post
        "OVERWRITE_REDIRECT_URI": get_config_vars()["OVERWRITE_REDIRECT_URI"],
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
    return (
        'You don\'t have valid permissions to edit MoUs. <a href="/logout">Logout</a>'
    )
