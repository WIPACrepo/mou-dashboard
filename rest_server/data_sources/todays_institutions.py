"""Tools for getting info on the state of today's institutions."""

import logging
from typing import Any

import universal_utils.types as uut
from krs import institutions as krs_institutions  # type: ignore[import]
from krs import token
from wipac_dev_tools import strtobool


def convert_krs_institution(
    experiment: str,
    inst: str,
    attrs: dict[str, str],
) -> list[uut.Institution]:
    """Convert from krs response data to list[uut.Institution]."""
    if not attrs:
        continue
    try:
        has_mou = strtobool(attrs.get("has_mou", "false"))
        if has_mou and "name" not in attrs:
            raise KeyError('"name" is required')
        if has_mou and "is_US" not in attrs:
            raise KeyError('"is_US" is required')
        return uut.Institution(
            short_name=inst,
            long_name=attrs.get("name", inst),
            is_us=strtobool(attrs.get("is_US", "false")),
            mou_list=[experiment] if has_mou else [],
            institution_lead_uid=attrs.get("institutionLeadUid", ""),
        )
    except Exception:
        logging.warning("bad inst attributes for inst %s", inst, exc_info=True)
        raise


async def request_krs_institutions() -> list[uut.Institution]:
    """Grab the master list of institutions along with their details."""
    rc = token.get_rest_client()

    all_insts = {}

    for experiment in ("IceCube", "IceCube-Gen2"):
        krs_experiment_insts = await krs_institutions.list_insts(
            experiment=experiment,
            filter_func=None,
            rest_client=rc,
        )
        for name, attrs in krs_experiment_insts.items():
            if not attrs:
                continue
            if name in all_insts:
                # if inst is in other experiment, use first attrs, but append `mou_list`
                all_insts[name].mou_list.append(name)
            else:
                all_insts[name] = convert_krs_institution(experiment, name, attrs)

    return list(all_insts.values())
