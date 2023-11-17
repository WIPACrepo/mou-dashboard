"""Tools for getting info on the state of today's institutions."""

import logging

import universal_utils.types as uut
from krs import institutions as krs_institutions  # type: ignore[import]
from krs import token
from wipac_dev_tools import strtobool


def convert_krs_institution(
    group: str,
    attrs: dict[str, str],
) -> uut.Institution:
    """Convert from krs response dict to an Institution instance."""
    name = group.removeprefix("/institutions/IceCube/")

    try:
        has_mou = strtobool(attrs.get("has_mou", "false"))
        if has_mou and "name" not in attrs:
            raise KeyError('"name" is required')
        if has_mou and "is_US" not in attrs:
            raise KeyError('"is_US" is required')
        return uut.Institution(
            short_name=name,
            long_name=attrs.get("name", name),
            is_us=strtobool(attrs.get("is_US", "false")),
            has_mou=has_mou,
            institution_lead_uid=attrs.get("institutionLeadUid", ""),
        )
    except Exception:
        logging.warning("bad inst attributes for inst %s", name, exc_info=True)
        raise


async def request_krs_institutions() -> list[uut.Institution]:
    """Grab the master list of institutions along with their details."""
    rc = token.get_rest_client()

    all_insts: dict[str, uut.Institution] = {}

    krs_experiment_insts = await krs_institutions.list_insts(
        experiment="IceCube",
        filter_func=None,
        rest_client=rc,
    )
    for group, attrs in krs_experiment_insts.items():
        if not attrs:
            continue
        inst = convert_krs_institution(group, attrs)
        all_insts[inst.short_name] = inst

    return list(all_insts.values())
