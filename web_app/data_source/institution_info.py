"""Static Institution Info Functions"""

import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, cast

from ..config import MAX_CACHE_MINS
from .utils import mou_request


@dataclass(frozen=True)
class Institution:
    """Hold minimal institution data."""

    short_name: str
    long_name: str
    is_us: bool
    has_mou: bool
    institution_lead_uid: str


@lru_cache()
def _cached_get_institutions_infos(timeframe: int) -> Dict[str, Institution]:
    """Cache is keyed by an int.

    The int is used to auto-expire/regenerate cache results.
    """
    # pylint:disable=unused-argument
    resp = cast(Dict[str, Dict[str, Any]], mou_request("GET", "/institution/today"))

    return {k: Institution(**v) for k, v in resp.items()}


def get_institutions_infos() -> Dict[str, Institution]:
    """Get a dict of all institutions with their info."""

    return _cached_get_institutions_infos(
        time.time() // (60 * MAX_CACHE_MINS),  # make cache hit expire after X mins
    )
