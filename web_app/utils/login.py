"""Handle user log-in and account info."""

import logging
from typing import Optional

from flask_login import UserMixin  # type: ignore[import]

from ..config import get_config_vars, login_manager


# Create User class with UserMixin
class User(UserMixin):  # type: ignore[misc]
    """User log-in manager."""

    class _MockAuth:
        """For testing purposes."""

        @staticmethod
        def lookup_user(user: "User", email: str, institution: str) -> "User":
            """For testing purposes."""
            user.name = email.split("@")[0]
            user.institution = institution
            user.is_admin = email.split("@")[1].upper() == "ADMIN"
            return user

        @staticmethod
        def login(email: str, pwd: str) -> None:
            """For testing purposes."""
            if not (email and "@" in email and pwd == "123456789"):
                raise Exception()

    def __init__(self) -> None:
        self.id = ""  # mandatory attribute  # pylint: disable=C0103
        self.name = ""
        self.email = ""
        self.institution = ""
        self.is_admin = False

    def __repr__(self) -> str:
        """Get str for logging."""
        return str(self.__dict__)

    @staticmethod
    def lookup_user(email: str, institution: str = "") -> "User":
        """Look-up user by their email.

        Assumes login has already occurred and email is valid.
        """
        user = User()
        user.id = email  # use email as the id
        user.email = email

        # for testing -- no auth server
        if get_config_vars()["NO_USER_AUTH_REQ"]:
            logging.info(f"Looking up user info via Mock-Auth: {user=}")
            user = User._MockAuth.lookup_user(user, email, institution)

        # auth
        else:
            logging.info(f"Looking up user info via Keycloak: {user=}")
            # TODO: replace w/ keycloak
            user = User._MockAuth.lookup_user(user, email, institution)

        logging.warning(f"User info: {user=}")
        return user

    @staticmethod
    def login(email: str, pwd: str, institution: str) -> Optional["User"]:
        """Login user, return User object if successful."""
        # TODO: refactor when keycloak

        # for testing -- no auth server
        if get_config_vars()["NO_USER_AUTH_REQ"]:
            logging.info(f"Verifying login via Mock-Auth: {email=}")
            try:
                User._MockAuth.login(email, pwd)
            except:  # noqa # pylint: disable=W0702 # shhh...
                logging.error(f"Bad user login: {email=}")
                return None

        # auth
        else:
            logging.info(f"Verifying login via LDAP: {email=}")
            # TODO: LDAP

        user = User.lookup_user(email, institution)

        # regular users must have an institution
        if (not user.is_admin) and (not institution):
            logging.error(f"User does not have an institution: {user.email=}")
            return None

        logging.warning(f"User verified: {user.email=}")
        return user


@login_manager.user_loader  # type: ignore[misc]
def load_user(user_id: str) -> UserMixin:
    """Reload the user object.

    This is the end point for `current_user`.
    """
    logging.warning(f"flask_login.current_user -> load_user(): {user_id=}")

    if not user_id:
        logging.warning("Using anonymous user AKA no log-in")
        return User()  # aka anonymous user

    return User.lookup_user(user_id)
