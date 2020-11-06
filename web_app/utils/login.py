"""Handle user log-in and account info."""

import logging
from typing import cast, Final, Optional

import ldap3  # type: ignore[import]
from flask_login import UserMixin  # type: ignore[import]

from ..config import ADMINS, login_manager

_LDAP_BASE: Final[str] = "ou=People,dc=icecube,dc=wisc,dc=edu"
_LDAP_URI: Final[str] = "ldaps://ldap-1.icecube.wisc.edu"


def _ldap_server() -> ldap3.Server:
    return ldap3.Server(_LDAP_URI, connect_timeout=5)


class InvalidLoginException(Exception):
    """Exception for an invalid login attempt."""


def _ldap_lookup_user(
    user: "User", institution: str, conn: Optional[ldap3.Connection] = None
) -> "User":
    """For testing purposes."""
    logging.debug(f"Looking up user info via LDAP ({user=})...")

    if not conn:
        conn = ldap3.Connection(_ldap_server(), auto_bind=True)
    conn.search(_LDAP_BASE, f"(uid={user.id})", attributes=["*"])
    info = conn.entries[0]
    logging.warning(f"{info=}")

    # name
    user.name = cast(str, info.cn.value)
    try:  # use full name
        if info.i3NickName.value:
            user.name = f"{info.i3NickName.value} {info.sn.value}"
    except ldap3.core.exceptions.LDAPCursorAttributeError:
        pass

    # institution
    user.institution = institution

    # admin status
    user.is_admin = user.id in ADMINS

    return user


def _ldap_try_login(uid: str, pwd: str) -> ldap3.Connection:
    """Try to get an LDAP connection.

    https://github.com/WIPACrepo/iceprod/blob/master/iceprod/server/rest/auth.py#L454
    https://www.programcreek.com/python/example/107948/ldap3.Connection
    """
    try:
        logging.debug(f"Verifying login via LDAP ({uid=})...")
        conn = ldap3.Connection(
            _ldap_server(), f"uid={uid},{_LDAP_BASE}", pwd, auto_bind=True
        )
        logging.debug(f"LDAP Successful! ({uid=})")
        return conn

    except ldap3.core.exceptions.LDAPException:
        logging.warning(f"Bad user login: {uid=}", exc_info=True)
        raise InvalidLoginException()


# Create User class with UserMixin
class User(UserMixin):  # type: ignore[misc]
    """User log-in manager."""

    def __init__(self) -> None:
        self.id = ""  # mandatory attribute  # pylint: disable=C0103
        self.name = ""
        self.institution = ""
        self.is_admin = False

    def __repr__(self) -> str:
        """Get str for logging."""
        return str(self.__dict__)

    @staticmethod
    def lookup_user(
        uid: str, institution: str = "", conn: Optional[ldap3.Connection] = None
    ) -> "User":
        """Look-up user by their uid.

        Assumes login has already occurred and uid is valid.
        """
        user = User()
        user.id = uid  # use uid as the id
        user = _ldap_lookup_user(user, institution, conn=conn)

        logging.info(f"User info: {user=}")
        return user

    @staticmethod
    def try_login(uid: str, pwd: str, institution: str) -> "User":
        """Login user, return User object.

        Raise InvalidLoginException if unsuccessful.

        # TODO: refactor when keycloak?
        """
        conn = _ldap_try_login(uid, pwd)
        user = User.lookup_user(uid, institution, conn)

        # non-admin users must have an institution
        if (not user.is_admin) and (not institution):
            logging.warning(f"User does not have an institution: {user.id=}")
            raise InvalidLoginException()

        logging.info(f"User verified: {user.id=}")
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
