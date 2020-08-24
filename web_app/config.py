"""Config file."""

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
    ],
)

server = app.server
app.config.suppress_callback_exceptions = True


# --------------------------------------------------------------------------------------
# Get constants from environment variables


config_env = from_environment(
    {
        "DBMS_SERVER_URL": "http://localhost:8080",
        "TOKEN_SERVER_URL": "http://localhost:8888",
    }
)

DBMS_SERVER_URL = config_env["DBMS_SERVER_URL"]
TOKEN_SERVER_URL = config_env["TOKEN_SERVER_URL"]
