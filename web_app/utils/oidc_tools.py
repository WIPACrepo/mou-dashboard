"""Handle user log-in and account info."""

from typing import Any, Dict, List, Optional, cast

from ..config import cache, oidc


class CurrentUser:
    """Wrap oidc's user info requests."""

    # TODO - cache, clear cache, etc.
    @staticmethod
    def _get_info() -> Dict[str, Any]:
        """Query OIDC."""
        return cast(
            Dict[str, Any],
            oidc.user_getinfo(["preferred_username", "email", "name", "groups"]),
        )

    @staticmethod
    def get_summary() -> Optional[Dict[str, Any]]:
        """Query OIDC."""
        if not CurrentUser.is_authenticated():
            return None
        return CurrentUser._get_info()

    @staticmethod
    def is_authenticated() -> bool:
        """Is the user authenticated (logged-in)?"""
        return bool(oidc.user_loggedin)

    @staticmethod
    def is_admin() -> bool:
        """Is the user an admin?"""
        try:
            return "/posix/mou-dashboard-admin" in CurrentUser._get_info()["groups"]
        except (KeyError, TypeError):
            return False

    @staticmethod
    def get_username() -> str:
        """Get the user's name."""
        return cast(str, CurrentUser._get_info()["preferred_username"])

    @staticmethod
    def get_institutions() -> List[str]:
        """Get the user's institution."""
        insts = []
        for group in CurrentUser._get_info()["groups"]:
            if group.startswith("/institutions/"):
                insts.append(group.split("/")[-1])

        # get rid of duplicates, like
        # "/institutions/IceCube/UW-Madison" -> "UW-Madison"
        # "/institutions/IceCube-Gen2/UW-Madison" -> "UW-Madison"

        return list(set(insts))
