"""Handle user log-in and account info."""

import logging
import re
from dataclasses import dataclass
from typing import Any, cast

import cachetools.func  # type: ignore[import]
import flask  # type: ignore[import]

from ..config import ENV, MAX_CACHE_MINS, oidc
from ..data_source import connections


@dataclass(frozen=True)
class UserInfo:
    """Hold user data."""

    preferred_username: str
    groups: list[str]


class CurrentUser:
    """Wrap oidc's user info requests."""

    @staticmethod
    @cachetools.func.ttl_cache(ttl=MAX_CACHE_MINS * 60)  # type: ignore[misc]
    def _cached_get_info(oidc_csrf_token: str) -> UserInfo:
        """Cache is keyed by the oidc session token."""
        # pylint:disable=unused-argument
        logging.warning(f"Cache Miss: CurrentUser._cached_get_info({oidc_csrf_token=})")
        resp: dict[str, Any] = oidc.user_getinfo(["preferred_username", "groups"])
        return UserInfo(**resp)

    @staticmethod
    def _get_info() -> UserInfo:
        """Query OIDC."""
        return cast(
            UserInfo, CurrentUser._cached_get_info(flask.session["oidc_csrf_token"])
        )

    @staticmethod
    def get_summary() -> dict[str, Any] | None:
        """Query OIDC."""
        if not CurrentUser.is_loggedin():
            return None
        return {
            "mou": {
                "is_authenticated": CurrentUser.is_loggedin_with_permissions(),
                "is_admin": CurrentUser.is_admin(),
                "get_username": CurrentUser.get_username(),
                "get_institutions": CurrentUser.get_institutions(),
            },
            "info": CurrentUser._get_info(),
        }

    @staticmethod
    def is_loggedin() -> bool:
        """Is the user logged-in?"""
        return bool(oidc.user_loggedin)

    @staticmethod
    def is_loggedin_with_permissions() -> bool:
        """Is the user authenticated (logged-in w/ permissions)?"""
        if not CurrentUser.is_loggedin():
            logging.debug("[USER_INFO] User is not logged in")
            return False

        if CurrentUser.is_admin():
            logging.debug("[USER_INFO] User is admin")
            return True

        if insts := CurrentUser.get_institutions():
            logging.debug(f"[USER_INFO] User has {len(insts)} institution(s)")
            return True

        logging.debug("[USER_INFO] User has no institutions, but is logged in")
        return False

    @staticmethod
    def is_admin() -> bool:
        """Is the user an admin?"""
        if ENV.DEBUG_AS_PI:
            return False
        try:
            return "/tokens/mou-dashboard-admin" in CurrentUser._get_info().groups
        except (KeyError, TypeError):
            return False

    @staticmethod
    def get_username() -> str:
        """Get the user's name."""
        return CurrentUser._get_info().preferred_username

    @staticmethod
    def get_institutions() -> list[str]:
        """Get the user's editable institutions."""

        # Ex: /institutions/IceCube/UW-Madison/mou-dashboard-editor
        # Ex: /institutions/IceCube/UW-Madison/_admin

        # also, get rid of duplicates, like
        # "/institutions/IceCube/UW-Madison/_admin" -> "UW-Madison"
        # "/institutions/IceCube-Gen2/UW-Madison/_admin" -> "UW-Madison"

        group_insts = set()
        for user_group in CurrentUser._get_info().groups:
            pattern = (
                r"/institutions/[^/]+/(?P<inst>[^/]+)/(mou-dashboard-editor|_admin)$"
            )
            if m := re.match(pattern, user_group):
                group_insts.add(m.groupdict()["inst"])

        if ENV.DEBUG_AS_PI:
            group_insts = set(ENV.DEBUG_AS_PI)

        # now, check if each of the institutions has an mou
        infos = connections.get_institutions_infos()
        editable_insts = []
        for short_name in group_insts:
            try:
                if not infos[short_name].has_mou:
                    logging.error(
                        f"User ({CurrentUser.get_username()}) belongs to {short_name},"
                        " but institution does not have an MOU (has_mou=false)"
                    )
                editable_insts.append(short_name)
            except KeyError:
                continue

        return editable_insts
