"""Utilities for MoU REST interfaces."""


import logging
from typing import Any, Dict

import requests

# local imports
from rest_tools.client import RestClient  # type: ignore

from ..config import CONFIG


def _rest_connection() -> RestClient:
    """Return REST Client connection object."""
    if CONFIG["TOKEN"]:
        token = CONFIG["TOKEN"]
    else:
        token_json = requests.get(CONFIG["TOKEN_REQUEST_URL"]).json()
        token = token_json["access"]

    rc = RestClient(CONFIG["REST_SERVER_URL"], token=token, timeout=5, retries=0)

    return rc


def _request(method: str, url: str, body: Any = None) -> Dict[str, Any]:
    logging.info(f"REQUEST :: {method} @ {url}, body: {body}")

    response: Dict[str, Any] = _rest_connection().request_seq(method, url, body)

    def log_it(key: str, val: Any) -> Any:
        if key == "table":
            return f"{len(val)} records"
        if isinstance(val, dict):
            return val.keys()
        return val

    logging.info(f"RESPONSE ({method} @ {url}, body: {body}) ::")
    for key, val in response.items():
        logging.info(f"> {key}")
        logging.debug(f"-> {str(type(val).__name__)}")
        logging.debug(f"-> {log_it(key, val)}")

    return response
