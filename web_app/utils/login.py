"""Handle user log-in and account info."""

import logging
from typing import Dict, Optional

from flask_login import UserMixin  # type: ignore[import]

from ..config import login_manager


def _mock_account_lookup(email: str) -> Dict[str, str]:
    inst = email.split("@")[1].upper()
    return {"institution": inst, "name": f"{inst}-User"}


# Create User class with UserMixin
class User(UserMixin):  # type: ignore[misc]
    """User log-in manager."""

    def __init__(self) -> None:
        self.id = ""  # mandatory attribute  # pylint: disable=C0103
        self.name = ""
        self.email = ""
        self.institution = ""

    @staticmethod
    def lookup_user(email: str) -> "User":
        """Look-up user by their email.

        Assumes login has already occurred and email is valid.
        """
        user = User()
        user.id = email  # use email as the id
        user.email = email

        # TODO: look up leader info w/ email
        response = _mock_account_lookup(email)
        user.name = response["name"]
        user.institution = response["institution"]

        return user

    @staticmethod
    def _ldap_login(email: str, pwd: str) -> bool:
        # TODO: look up user w/ password
        if "@" in email and pwd == "123456789":
            return True
        return False

    @staticmethod
    def login(email: str, pwd: str) -> Optional["User"]:
        """Login user, return User object if successful."""
        if User._ldap_login(email, pwd):
            logging.info(f"Login: {email}")
            return User.lookup_user(email)

        logging.info(f"Bad login: {email}")
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
