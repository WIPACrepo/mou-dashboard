"""Utilities for MoU REST interfaces."""


import copy
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Final, cast

import cachetools.func
import flask
import requests
import universal_utils.types as uut

# local imports
from rest_tools.client import ClientCredentialsAuth, RestClient

from ..config import ENV, MAX_CACHE_MINS, oidc


class DataSourceException(Exception):
    """Exception class for bad data-source requests."""


def _rest_connection() -> RestClient:
    """Return REST Client connection object."""
    if ENV.CI_TEST:
        logging.warning("CI TEST ENV - no auth to REST API")
        rc = RestClient(ENV.REST_SERVER_URL, timeout=5, retries=0)
    else:
        with open(ENV.OIDC_CLIENT_SECRETS) as f:
            oidc_client = json.load(f).get("web", {})
        rc = ClientCredentialsAuth(
            ENV.REST_SERVER_URL,
            token_url=oidc_client.get("issuer"),
            client_id=oidc_client.get("client_id"),
            client_secret=oidc_client.get("client_secret"),
        )

    return rc


def _get_log_body(method: str, url: str, body: Any) -> str:
    log_body = body

    if method == "POST" and url.startswith("/table/data/"):
        log_body = copy.deepcopy(body)
        length: Final[int] = 10
        b64 = log_body["base64_file"]
        omitted = len(b64) - length
        log_body["base64_file"] = f"{b64[:length]}... ({omitted} chars omitted)"

    return str(log_body)


def mou_request(method: str, url: str, body: Any = None) -> dict[str, Any]:
    """Make a request to the MoU REST server."""
    log_body = _get_log_body(method, url, body)
    logging.info(f"REQUEST :: {method} @ {url}, body: {log_body}")

    try:
        response: dict[str, Any] = _rest_connection().request_seq(method, url, body)
    except requests.exceptions.HTTPError as e:
        logging.exception(f"EXCEPTED: {e}")
        raise DataSourceException(str(e))

    def log_it(key: str, val: Any) -> Any:
        if key == "table":
            return f"{len(val)} records"
        if isinstance(val, dict):
            return val.keys()
        return val

    logging.info(f"RESPONSE ({method} @ {url}, body: {log_body}) ::")
    for key, val in response.items():
        logging.debug(f"> {key}")
        logging.debug(f"-> {str(type(val).__name__)}")
        logging.debug(f"-> {log_it(key, val)}")

    return response


#
# Static Institution Info Functions
#


@cachetools.func.ttl_cache(ttl=MAX_CACHE_MINS * 60)
def _cached_get_todays_institutions_infos() -> dict[str, uut.Institution]:
    logging.warning("Cache Miss: _cached_get_institutions_infos()")
    resp = cast(dict[str, dict[str, Any]], mou_request("GET", "/institution/today"))
    return {k: uut.Institution(**v) for k, v in resp.items()}


def get_todays_institutions_infos() -> dict[str, uut.Institution]:
    """Get a dict of all institutions with their info, accurate as of today."""
    return _cached_get_todays_institutions_infos()


#
# Handle user log-in and account info
#


@dataclass(frozen=True)
class UserInfo:
    """Hold user data."""

    preferred_username: str
    groups: list[str]
    access_token: str


class CurrentUser:
    """Wrap oidc's user info requests."""

    @staticmethod
    @cachetools.func.ttl_cache(ttl=((5 * 60) - 1))  # access token has 5m lifetime
    def _cached_get_info(oidc_csrf_token: str) -> UserInfo:
        """Cache is keyed by the oidc session token."""
        # pylint:disable=unused-argument
        logging.warning(f"Cache Miss: CurrentUser._cached_get_info({oidc_csrf_token=})")
        resp: dict[str, Any] = oidc.user_getinfo(["preferred_username", "groups"])
        resp["access_token"] = oidc.get_access_token()
        return UserInfo(**resp)

    @staticmethod
    def _get_info() -> UserInfo:
        """Query OIDC."""
        if ENV.CI_TEST:
            return UserInfo(
                "arnold.schwarzenegger", ["/tokens/mou-dashboard-admin"], "XYZ"
            )

        return CurrentUser._cached_get_info(flask.session["oidc_csrf_token"])

    @staticmethod
    def get_summary() -> None | dict[str, Any]:
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
        if ENV.CI_TEST:
            return True
        return bool(oidc.user_loggedin)

    @staticmethod
    def is_loggedin_with_permissions() -> bool:
        """Is the user authenticated (logged-in w/ permissions)?"""
        if not CurrentUser.is_loggedin():
            return False

        if CurrentUser.is_admin():
            return True

        if CurrentUser.get_institutions():
            return True

        return False

    @staticmethod
    def is_admin() -> bool:
        """Is the user an admin?"""
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

        # NOTE: an institution admin is not a dashboard admin

        # Ex: /institutions/IceCube/UW-Madison/mou-dashboard-editor
        # Ex: /institutions/IceCube/UW-Madison/_admin

        # also, get rid of duplicates, like
        # "/institutions/IceCube/UW-Madison/_admin" -> "UW-Madison"
        # "/institutions/IceCube-Gen2/UW-Madison/_admin" -> "UW-Madison"

        user_insts = set()
        for user_group in CurrentUser._get_info().groups:
            pattern = (
                r"/institutions/[^/]+/(?P<inst>[^/]+)/(mou-dashboard-editor|_admin)$"
            )
            if m := re.match(pattern, user_group):
                user_insts.add(m.groupdict()["inst"])

        # now, check if each of the institutions has an mou
        all_insts_infos = get_todays_institutions_infos()
        user_mou_insts = []
        for inst_short_name in user_insts:
            if inst_short_name not in all_insts_infos:
                logging.error(
                    f"User ({CurrentUser.get_username()}) belongs to {inst_short_name},"
                    " but institution is not in today's list of institutions."
                )
                continue
            if not all_insts_infos[inst_short_name].has_mou:
                logging.error(
                    f"User ({CurrentUser.get_username()}) belongs to {inst_short_name},"
                    " but institution does not have an MOU (has_mou=false)"
                )
                continue  # technically not needed since this inst couldn't be selected to begin with
            user_mou_insts.append(inst_short_name)

        return user_mou_insts

    @staticmethod
    def get_access_token() -> str:
        """Retrieve the logged-in user's access token."""
        return CurrentUser._get_info().access_token
