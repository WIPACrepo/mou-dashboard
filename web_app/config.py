"""Config file."""

import logging
import os
from typing import Optional, TypedDict

import dash  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import flask
from flask_login import LoginManager, UserMixin  # type: ignore[import]

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
login_manager = LoginManager()
login_manager.init_app(server)


# Create User class with UserMixin
# class User(UserMixin, base):
class User(UserMixin):  # type: ignore[misc]
    """User log-in manager."""

    def __init__(self) -> None:
        self.id: Optional[int] = None  # pylint: disable=C0103
        self.username = ""
        self.email = ""
        # self.password = ''
        self.institution = ""

    @staticmethod
    def login(username: str, password: str) -> "User":
        # TODO: look up user w/ password
        user = User()
        user.id = 1
        user.username = "ric"
        user.email = "UW"
        # user.password = "UW"
        user.institution = "UW"
        return user


@login_manager.user_loader  # type: ignore[misc]
def load_user(user_id: str) -> UserMixin:
    """Callback to reload the user object."""
    return User()


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
