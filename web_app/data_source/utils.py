"""Utilities for MOU REST interfaces."""


import copy
import logging
import time
from typing import Any, Dict, Final

import requests
from rest_tools.client import RestClient

from ..config import ENV


class DataSourceException(Exception):
    """Exception class for bad data-source requests."""


def _rest_connection() -> RestClient:
    """Return REST Client connection object."""
    if ENV.TOKEN:
        token = ENV.TOKEN
    else:
        token_json = requests.get(ENV.TOKEN_REQUEST_URL).json()
        token = token_json["access"]

    rc = RestClient(ENV.REST_SERVER_URL, token=token, timeout=30, retries=0)

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


def mou_request(method: str, url: str, body: Any = None) -> Dict[str, Any]:
    """Make a request to the MOU REST server."""
    log_body = _get_log_body(method, url, body)
    logging.info(f"REQUEST :: {method} @ {url}, body: {log_body}")

    if ENV.DEBUG:
        time.sleep(0.1)

    try:
        response: Dict[str, Any] = _rest_connection().request_seq(method, url, body)
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
