"""Config file."""

import logging
import os
from typing import TypedDict
from urllib.parse import urljoin

import dash  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import flask
from flask_caching import Cache  # type: ignore[import]
from flask_login import LoginManager  # type: ignore[import]

# local imports
from rest_tools.server.config import from_environment  # type: ignore[import]

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
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css",
    ],
)

# config
server = app.server
app.config.suppress_callback_exceptions = True
server.config.update(SECRET_KEY=os.urandom(12))


# Setup the LoginManager for the server
# NOTE: https://github.com/RafaelMiquelino/dash-flask-login
cache = Cache(app.server, config={"CACHE_TYPE": "simple"})
login_manager = LoginManager()
login_manager.init_app(server)
ADMINS = ["eevans", "desiati", "dschultz", "cvakhnina"]


# --------------------------------------------------------------------------------------
# configure config_vars


class ConfigVarsTypedDict(TypedDict, total=False):
    """Global configuration-variable types."""

    REST_SERVER_URL: str
    TOKEN_SERVER_URL: str
    WEB_SERVER_PORT: int
    AUTH_PREFIX: str
    TOKEN_REQUEST_URL: str
    TOKEN: str
    NO_USER_AUTH_REQ: bool


def get_config_vars() -> ConfigVarsTypedDict:
    """Get the global configuration variables."""
    config_vars: ConfigVarsTypedDict = from_environment(
        {
            "REST_SERVER_URL": "http://localhost:8080",
            "TOKEN_SERVER_URL": "http://localhost:8888",
            "WEB_SERVER_PORT": 8050,
            "AUTH_PREFIX": "mou",
            "TOKEN": "",
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
