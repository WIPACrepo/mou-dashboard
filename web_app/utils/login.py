"""Handle user log-in and account info."""

import logging

import ldap3  # type: ignore[import]
from flask_login import UserMixin  # type: ignore[import]

from ..config import get_config_vars, login_manager


class InvalidLoginException(Exception):
    """Exception for an invalid login attempt."""


def mock_lookup_user(user: "User", email: str, institution: str) -> "User":
    """For testing purposes."""
    user.name = email.split("@")[0]
    user.institution = institution
    user.is_admin = email.split("@")[1].upper() == "ADMIN"
    return user


def mock_try_login(email: str, pwd: str) -> None:
    """For testing purposes."""
    logging.debug(f"Verifying login via Mock-Auth ({email=})...")
    if not (email and "@" in email and pwd == "123456789"):
        logging.warning(f"Bad user login: {email=}")
        raise InvalidLoginException()


def ldap_try_login(email: str, pwd: str) -> None:
    """Try to get an LDAP connection.

    # https://github.com/WIPACrepo/iceprod/blob/master/iceprod/server/rest/auth.py#L454
    """
    logging.debug(f"Verifying login via LDAP ({email=})...")
    try:
        ldap3.Connection(
            ldap3.Server("ldaps://ldap-1.icecube.wisc.edu", connect_timeout=5),
            f"uid={email},ou=People,dc=icecube,dc=wisc,dc=edu",
            pwd,
            auto_bind=True,
        )
    except ldap3.core.exceptions.LDAPException:
        logging.warning(f"Bad user login: {email=}", exc_info=True)
        raise InvalidLoginException()


# Create User class with UserMixin
class User(UserMixin):  # type: ignore[misc]
    """User log-in manager."""

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

        if get_config_vars()["NO_USER_AUTH_REQ"]:
            # for testing -- no auth server
            logging.debug(f"Looking up user info via Mock-Auth: {user=}")
            user = mock_lookup_user(user, email, institution)
        else:
            # w/ auth
            # logging.debug(f"Looking up user info via Keycloak: {user=}")
            # TODO: replace w/ keycloak
            logging.error(f"Keycloak is not set up, using Mock-Auth: {user=}")
            user = mock_lookup_user(user, email, institution)

        logging.info(f"User info: {user=}")
        return user

    @staticmethod
    def try_login(email: str, pwd: str, institution: str) -> "User":
        """Login user, return User object.

        Raise InvalidLoginException if unsuccessful.
        """
        # TODO: refactor when keycloak?

        # Login
        if get_config_vars()["NO_USER_AUTH_REQ"]:
            mock_try_login(email, pwd)
        else:
            ldap_try_login(email, pwd)

        # Get User Info
        user = User.lookup_user(email, institution)

        # non-admin users must have an institution
        if (not user.is_admin) and (not institution):
            logging.warning(f"User does not have an institution: {user.email=}")
            raise InvalidLoginException()

        logging.info(f"User verified: {user.email=}")
        return user


@login_manager.user_loader  # type: ignore[misc]
def load_user(user_id: str) -> UserMixin:
    """Reload the user object.

    This is the end point for `current_user`.
    """
    logging.info(f"flask_login.current_user -> load_user(): {user_id=}")

    if not user_id:
        logging.info("Using anonymous user AKA no log-in")
        return User()  # aka anonymous user

    return User.lookup_user(user_id)
