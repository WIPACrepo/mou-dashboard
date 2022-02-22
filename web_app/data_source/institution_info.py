"""Static Institution Info Functions"""

from dataclasses import dataclass
from typing import Any, Dict, cast

from .utils import mou_request


@dataclass(frozen=True)
class Institution:
    """Hold minimal institution data."""

    short_name: str
    long_name: str
    is_us: bool
    has_mou: bool
    institution_lead_uid: str


def get_institutions_infos() -> Dict[str, Institution]:
    """Get a dict of all institutions with their info."""
    resp = cast(Dict[str, Dict[str, Any]], mou_request("GET", "/institution/today"))

    infos = {k: Institution(**v) for k, v in resp.items()}

    return infos
