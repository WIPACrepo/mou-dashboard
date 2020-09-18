"""Utility functions for the REST server interface."""


from typing import cast

# local imports
from keycloak_setup.icecube_setup import ICECUBE_INSTS  # type: ignore[import]

from .. import table_config as tc
from .types import Record, Table


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


# TODO: move to front-end?
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


def insert_total_rows(table: Table) -> Table:
    """Add rows with totals of each category (cascadingly)."""

    ####
    def grab_a_total(
        l2: str = "", l3: str = "", fund_src: str = "", region: str = ""
    ) -> float:
        return sum(
            float(r[tc.FTE])
            for r in table
            if r
            and tc.TOTAL_COL not in r.keys()  # skip any total rows
            and r[tc.FTE]  # skip blanks (also 0s)
            and (not l2 or r[tc.WBS_L2] == l2)
            and (not l3 or r[tc.WBS_L3] == l3)
            and (not fund_src or r[tc.SOURCE_OF_FUNDS_US_ONLY] == fund_src)
            and (not region or r[tc.US_NON_US] == region)
        )

    for l2_cat in tc.L2_CATEGORIES:
        for l3_cat in tc.L3_CATEGORIES_BY_L2[l2_cat]:
            for region in [tc.US, tc.NON_US]:

                # add US/Non-US
                table.append(
                    {
                        tc.WBS_L2: l2_cat,
                        tc.WBS_L3: l3_cat,
                        tc.US_NON_US: region,
                        tc.TOTAL_COL: f"L3 {region} total | {l3_cat}".upper(),
                        tc.NSF_MO_CORE: grab_a_total(
                            l2=l2_cat,
                            l3=l3_cat,
                            fund_src=tc.NSF_MO_CORE,
                            region=region,
                        ),
                        tc.NSF_BASE_GRANTS: grab_a_total(
                            l2=l2_cat,
                            l3=l3_cat,
                            fund_src=tc.NSF_BASE_GRANTS,
                            region=region,
                        ),
                        tc.US_IN_KIND: grab_a_total(
                            l2=l2_cat,
                            l3=l3_cat,
                            fund_src=tc.US_IN_KIND,
                            region=region,  #
                        ),
                        tc.NON_US_IN_KIND: grab_a_total(
                            l2=l2_cat,
                            l3=l3_cat,
                            fund_src=tc.NON_US_IN_KIND,
                            region=region,
                        ),
                        tc.GRAND_TOTAL: grab_a_total(
                            l2=l2_cat, l3=l3_cat, region=region
                        ),
                    }
                )

            # add L3
            table.append(
                {
                    tc.WBS_L2: l2_cat,
                    tc.WBS_L3: l3_cat,
                    tc.TOTAL_COL: f"L3 total | {l3_cat}".upper(),
                    tc.NSF_MO_CORE: grab_a_total(
                        l2=l2_cat, l3=l3_cat, fund_src=tc.NSF_MO_CORE
                    ),  # #
                    tc.NSF_BASE_GRANTS: grab_a_total(
                        l2=l2_cat, l3=l3_cat, fund_src=tc.NSF_BASE_GRANTS
                    ),
                    tc.US_IN_KIND: grab_a_total(
                        l2=l2_cat, l3=l3_cat, fund_src=tc.US_IN_KIND
                    ),  # ##
                    tc.NON_US_IN_KIND: grab_a_total(
                        l2=l2_cat, l3=l3_cat, fund_src=tc.NON_US_IN_KIND
                    ),
                    tc.GRAND_TOTAL: grab_a_total(l2=l2_cat, l3=l3_cat),
                }
            )

        # add L2
        table.append(
            {
                tc.WBS_L2: l2_cat,
                tc.TOTAL_COL: f"L2 total | {l2_cat}".upper(),
                tc.NSF_MO_CORE: grab_a_total(l2=l2_cat, fund_src=tc.NSF_MO_CORE),
                tc.NSF_BASE_GRANTS: grab_a_total(
                    l2=l2_cat, fund_src=tc.NSF_BASE_GRANTS
                ),
                tc.US_IN_KIND: grab_a_total(l2=l2_cat, fund_src=tc.US_IN_KIND),
                tc.NON_US_IN_KIND: grab_a_total(l2=l2_cat, fund_src=tc.NON_US_IN_KIND),
                tc.GRAND_TOTAL: grab_a_total(l2=l2_cat),
            }
        )

    # Grand Total
    table.append({tc.TOTAL_COL: "GRAND TOTAL", tc.GRAND_TOTAL: grab_a_total()})

    return table
