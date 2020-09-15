"""Utility functions for the REST server interface."""


from typing import cast

# local imports
from keycloak_setup.icecube_setup import ICECUBE_INSTS  # type: ignore[import]

from .. import table_config as tc
from .types import Record


def remove_on_the_fly_fields(record: Record) -> Record:
    """Remove (del) any fields that are only to be calculated on-the-fly."""
    for field in record.copy().keys():
        if field in tc.ON_THE_FLY_FIELDS:
            # copy over grand total to FTE
            if (field == tc.GRAND_TOTAL) and (tc.FTE not in record.keys()):
                record[tc.FTE] = record[field]
            # remove
            del record[field]

    return record


def _get_fte_subcolumn(record: Record) -> str:
    source = record[tc.SOURCE_OF_FUNDS_US_ONLY]
    return cast(str, source)


def _us_or_non_us(institution: str) -> str:
    for inst in ICECUBE_INSTS.values():
        if inst["abbreviation"] == institution:
            if inst["is_US"]:
                return tc.US
            return tc.NON_US
    return ""


def add_on_the_fly_fields(record: Record) -> Record:
    """Add fields that are only to be calculated on-the-fly."""
    record = remove_on_the_fly_fields(record)

    # FTE fields
    if tc.FTE in record.keys():
        record[_get_fte_subcolumn(record)] = record[tc.FTE]
        record[tc.GRAND_TOTAL] = record[tc.FTE]

    # US-only fields
    inst = cast(str, record[tc.INSTITUTION])
    record[tc.US_NON_US] = _us_or_non_us(inst)
    if record[tc.US_NON_US] == tc.NON_US:
        record[tc.SOURCE_OF_FUNDS_US_ONLY] = tc.NON_US_IN_KIND

    return record
