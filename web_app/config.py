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
# NOTE: https://github.com/RafaelMiquelino/dash-flask-login
login_manager = LoginManager()
login_manager.init_app(server)


# Create User class with UserMixin
class User(UserMixin):  # type: ignore[misc]
    """User log-in manager."""

    def __init__(self) -> None:
        self.id = ""  # pylint: disable=C0103
        self.name = ""
        self.email = ""
        self.institution = ""

    @staticmethod
    def lookup_user(email: str) -> "User":
        """Look-up user by their email."""
        user = User()
        # TODO: look up leader info
        user.id = email
        user.name = "Ric Evans"
        user.email = email
        user.institution = "UW"
        return user

    @staticmethod
    def _ldap_login(email: str, pwd: str) -> bool:
        # TODO: look up user w/ password
        if email == "ric@mail" and pwd == "pwd":
            return True
        return False

    @staticmethod
    def login(email: str, pwd: str) -> Optional["User"]:
        """Login user, return User object if successful."""
        if User._ldap_login(email, pwd):
            logging.info(f"Login: {email} | {pwd}")
            return User.lookup_user(email)

        logging.info(f"Bad login: {email} | {pwd}")
        return None


@login_manager.user_loader  # type: ignore[misc]
def load_user(user_id: str) -> UserMixin:
    """Reload the user object.

    This is the end point for `current_user`.
    """
    logging.warning(f"Grabbing user {user_id}")
    if user_id:
        return User.lookup_user(user_id)
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
