"""Tools for getting info on the state of today's institutions."""

from dataclasses import dataclass
from distutils.util import strtobool
from typing import Any, Dict, List

from krs import institutions as krs_institutions  # type: ignore[import]
from krs import token


@dataclass(frozen=True)
class Institution:
    """Hold minimal institution data."""

    short_name: str
    long_name: str
    is_us: bool
    has_mou: bool


def convert_krs_institutions(response: Dict[str, Any]) -> List[Institution]:
    """Convert from krs response data to List[Institution]."""
    insts: List[Institution] = []
    for inst, attrs in response.items():
        insts.append(
            Institution(
                short_name=inst,
                long_name=attrs["name"],
                is_us=bool(strtobool(attrs["is_US"])),
                has_mou=bool(strtobool(attrs["has_mou"])),
            )
        )
    return insts


async def request_krs_institutions() -> List[Institution]:
    """Grab the master list of institutions along with their details."""
    rc = token.get_rest_client()

    response = await krs_institutions.list_insts_flat(rest_client=rc)

    return convert_krs_institutions(response)
