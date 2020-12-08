"""Handle user log-in and account info."""

import logging
from typing import cast, Dict, Final

import ldap3  # type: ignore[import]
from flask_login import UserMixin  # type: ignore[import]

from ..config import ADMINS, login_manager, user_lookup_cache
from . import types

_LDAP_BASE: Final[str] = "ou=People,dc=icecube,dc=wisc,dc=edu"
_LDAP_URI: Final[str] = "ldaps://ldap-1.icecube.wisc.edu"


def _ldap_server() -> ldap3.Server:
    return ldap3.Server(_LDAP_URI, connect_timeout=5)


def _ldap_uid(uid: str) -> str:
    """Little hack to launch into non-admin mode using an admin account."""
    return uid.strip("~")


class InvalidUsernameException(Exception):
    """Exception for an invalid login/username."""


class InvalidPasswordException(Exception):
    """Exception for an invalid login/password."""


class NoUserInstitutionException(Exception):
    """Exception for login when user does not have an institution."""


def _ldap_lookup_user(uid: str) -> "User":
    """Look up user info via LDAP."""
    user = User()
    user.id = uid  # use uid as the id

    conn = ldap3.Connection(_ldap_server(), auto_bind=True)
    conn.search(_LDAP_BASE, f"(uid={_ldap_uid(user.id)})", attributes=["*"])
    info = conn.entries[0]

    # name
    user.name = cast(str, info.cn.value)
    try:  # try to build full nickname
        if info.i3NickName.value:
            user.name = f"{info.i3NickName.value} {info.sn.value}"
    except ldap3.core.exceptions.LDAPCursorAttributeError:
        pass

    # institution
    # user.institution = ... # TODO: now, this is set in login() callback

    # admin status
    user.is_admin = user.id in ADMINS

    return user


def _ldap_try_login(uid: str, pwd: str) -> None:
    """Try to get an LDAP connection.

    https://github.com/WIPACrepo/iceprod/blob/master/iceprod/server/rest/auth.py#L454
    https://www.programcreek.com/python/example/107948/ldap3.Connection
    """
    ldap3.Connection(
        _ldap_server(), f"uid={_ldap_uid(uid)},{_LDAP_BASE}", pwd, auto_bind=True
    )
    logging.debug(f"LDAP Successful! ({uid=})")


# Create User class with UserMixin
class User(UserMixin):  # type: ignore[misc]
    """User log-in manager."""

    INSTITUTION_WORKAROUND: Dict[str, str] = {}  # TODO: remove when keycloak

    def __init__(self) -> None:
        self.id = ""  # mandatory attribute  # pylint: disable=C0103
        self.name = ""
        self.institution = ""
        self.is_admin = False

    def __repr__(self) -> str:
        """Get str for logging."""
        return str(self.__dict__)

    @staticmethod
    @user_lookup_cache.memoize(timeout=60 * 60 * 24)  # type: ignore[misc]
    def lookup_user(uid: str) -> "User":
        """Look-up user by their uid.

        Assumes login has already occurred and uid is valid.
        """
        logging.debug(f"Looking up user info via LDAP ({uid=})...")

        try:
            user = _ldap_lookup_user(uid)
        except (IndexError, ldap3.core.exceptions.LDAPException):
            raise InvalidUsernameException()

        # TODO: remove when keycloak
        if not user.is_admin:
            user.institution = User.INSTITUTION_WORKAROUND[uid]

        logging.info(f"User info: {user=}")
        return user

    @staticmethod
    def try_login(uid: str, pwd: str, inst: types.DashVal) -> "User":
        """Login user, return User object.

        Raise InvalidLoginException if unsuccessful.

        # TODO: remove inst when keycloak
        """
        logging.debug(f"Verifying login via LDAP ({uid=})...")

        # users must have an institution
        inst = inst if isinstance(inst, str) else ""
        if not inst:
            logging.warning(f"User does not have an institution: {uid=}")
            raise NoUserInstitutionException()

        # TODO: remove when keycloak
        logging.debug(
            f"Using workaround BEFORE: {uid=} {inst=} {User.INSTITUTION_WORKAROUND=}"
        )
        User.INSTITUTION_WORKAROUND[uid] = inst
        logging.debug(
            f"Using workaround AFTER: {uid=} {inst=} {User.INSTITUTION_WORKAROUND=}"
        )

        # Log In
        try:
            _ldap_try_login(uid, pwd)
        except ldap3.core.exceptions.LDAPException:
            # was this a bad username or a bad password?
            try:
                User.lookup_user(uid)
            except InvalidUsernameException:
                logging.warning(f"Bad login (username): {uid=}")
                raise
            else:
                logging.warning(f"Bad login (password): {uid=}")
                raise InvalidPasswordException()

        # User info
        user = User.lookup_user(uid)

        logging.info(f"User verified: {user=}")
        return cast(User, user)


@login_manager.user_loader  # type: ignore[misc]
def load_user(user_id: str) -> UserMixin:
    """Reload the user object.

    This is the end point for `current_user`.
    """
    logging.info(f"flask_login.current_user -> load_user() ({user_id=}) ...")

    if not user_id:
        logging.info("Using anonymous user AKA no log-in")
        return User()  # aka anonymous user

    user = User.lookup_user(user_id)
    logging.error(f"Loaded user: {user=}")
    return user
