"""Config file."""

import dash  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import flask

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

DBMS_SERVER_URL = "http://localhost:8080"
TOKEN_SERVER_URL = "http://localhost:8888"
