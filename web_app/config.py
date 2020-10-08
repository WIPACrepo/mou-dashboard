"""Config file."""

import logging
import os
from typing import Any, cast, Dict, TypedDict
from urllib.parse import urljoin

import dash  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import flask
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
    ],
)

# config
server = app.server
app.config.suppress_callback_exceptions = True
server.config.update(SECRET_KEY=os.urandom(12))


# Setup the LoginManager for the server
# NOTE: https://github.com/RafaelMiquelino/dash-flask-login
login_manager = LoginManager()
login_manager.init_app(server)


# --------------------------------------------------------------------------------------
# configure CONFIG global


class _ConfigTypedDict(TypedDict, total=False):
    REST_SERVER_URL: str
    TOKEN_SERVER_URL: str
    WEB_SERVER_PORT: int
    AUTH_PREFIX: str
    TOKEN_REQUEST_URL: str
    TOKEN: str


CONFIG: _ConfigTypedDict = {
    "REST_SERVER_URL": "http://localhost:8080",
    "TOKEN_SERVER_URL": "http://localhost:8888",
    "WEB_SERVER_PORT": 8050,
    "AUTH_PREFIX": "mou",
    "TOKEN": "",
}


def update_config_global() -> Dict[str, Any]:
    """Update `CONFIG` using environment variables."""
    global CONFIG  # pylint: disable=W0603

    config_vars = from_environment(CONFIG)
    config_vars["TOKEN_REQUEST_URL"] = urljoin(
        config_vars["TOKEN_SERVER_URL"],
        f"token?scope={config_vars['AUTH_PREFIX']}:admin",
    )

    CONFIG.update(config_vars)
    _log_config()

    return cast(Dict[str, Any], config_vars)


def _log_config() -> None:
    """Log the `CONFIG` dict, key-value."""
    for key, val in CONFIG.items():
        logging.info(f"{key} \t {val}")
