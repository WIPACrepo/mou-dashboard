"""Config file."""

import logging
import os
from typing import Optional, TypedDict

import dash  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import flask
from flask_login import LoginManager  # type: ignore[import]

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
# Constants


class _ConfigTypedDict(TypedDict):
    REST_SERVER_URL: str
    TOKEN_SERVER_URL: str
    WEB_SERVER_PORT: int
    AUTH_PREFIX: str


CONFIG: _ConfigTypedDict = {
    "REST_SERVER_URL": "http://localhost:8080",
    "TOKEN_SERVER_URL": "http://localhost:8888",
    "WEB_SERVER_PORT": 8050,
    "AUTH_PREFIX": "mou",
}


def log_config() -> None:
    """Log the CONFIG dict, key-value."""
    for key, val in CONFIG.items():
        logging.info(f"{key} \t {val}")
