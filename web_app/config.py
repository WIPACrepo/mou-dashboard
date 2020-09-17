"""Config file."""

import logging

import dash  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import flask

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

server = app.server
app.config.suppress_callback_exceptions = True


# --------------------------------------------------------------------------------------
# Get constants from environment variables


_config_env = from_environment(
    {
        "MOU_REST_SERVER_URL": "http://localhost:8080",
        "MOU_TOKEN_SERVER_URL": "http://localhost:8888",
        "MOU_WEB_SERVER_PORT": 8050,
        "MOU_AUTH_PREFIX": "mou",
    }
)


REST_SERVER_URL = _config_env["MOU_REST_SERVER_URL"]
TOKEN_SERVER_URL = _config_env["MOU_TOKEN_SERVER_URL"]
WEB_SERVER_PORT = int(_config_env["MOU_WEB_SERVER_PORT"])
AUTH_PREFIX = _config_env["MOU_AUTH_PREFIX"]


def log_environment() -> None:
    """Log the environment variables."""
    for name in _config_env:
        logging.info(f"{name} \t {_config_env[name]}")
