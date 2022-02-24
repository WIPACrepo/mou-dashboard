"""Static Institution Info Functions"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, cast

import cachetools.func  # type: ignore[import]

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


@cachetools.func.ttl_cache(ttl=MAX_CACHE_MINS * 60)  # type: ignore[misc]
def _cached_get_institutions_infos() -> Dict[str, Institution]:
    logging.warning("Cache Miss: _cached_get_institutions_infos()")
    resp = cast(Dict[str, Dict[str, Any]], mou_request("GET", "/institution/today"))
    return {k: Institution(**v) for k, v in resp.items()}


def get_institutions_infos() -> Dict[str, Institution]:
    """Get a dict of all institutions with their info."""
    return cast(Dict[str, Institution], _cached_get_institutions_infos())
