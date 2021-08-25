"""Utility functions for the REST server interface."""

from decimal import Decimal
from typing import cast

from ..databases import table_config as tc
from . import types


def remove_on_the_fly_fields(record: types.Record) -> types.Record:
    """Remove (del) any fields that are only to be calculated on-the-fly."""
    tc_reader = tc.TableConfigDatabaseClient()

    for field in record.copy().keys():
        if field in tc_reader.get_on_the_fly_fields():
            # copy over grand total to FTE
            if (field == tc.GRAND_TOTAL) and (tc.FTE not in record.keys()):
                record[tc.FTE] = record[field]
            # remove
            del record[field]

    return record


def _get_fte_subcolumn(record: types.Record) -> str:
    source = record[tc.SOURCE_OF_FUNDS_US_ONLY]
    return cast(str, source)


def add_on_the_fly_fields(record: types.Record) -> types.Record:
    """Add fields that are only to be calculated on-the-fly."""
    record = remove_on_the_fly_fields(record)

    # FTE fields
    if tc.FTE in record.keys():
        try:
            record[_get_fte_subcolumn(record)] = record[tc.FTE]
        except KeyError:
            pass
        record[tc.GRAND_TOTAL] = record[tc.FTE]

    # US-only fields
    inst = cast(str, record[tc.INSTITUTION])
    record[tc.US_NON_US] = tc.TableConfigDatabaseClient().us_or_non_us(inst)
    if record[tc.US_NON_US] == tc.NON_US:
        record[tc.SOURCE_OF_FUNDS_US_ONLY] = tc.NON_US_IN_KIND

    return record


def get_total_rows(
    wbs_l1: str,
    table: types.Table,
    only_totals_w_data: bool = False,
    with_us_non_us: bool = True,
) -> types.Table:
    """Calculate rows with totals of each category (cascadingly).

    Arguments:
        table {types.Table} -- table with records (only read)

    Keyword Arguments:
        only_totals_w_data {bool} -- exclude totals that only have 0s (default: {False})

    Returns:
        types.Table -- a new table of rows with totals
    """
    totals: types.Table = []

    def grab_a_total(  # pylint: disable=C0103
        l2: str = "", l3: str = "", fund_src: str = "", region: str = ""
    ) -> float:
        return float(
            sum(
                Decimal(str(r[tc.FTE]))  # avoid floating point loss
                for r in table
                if r
                and tc.TOTAL_COL not in r.keys()  # skip any total rows
                and r[tc.FTE]  # skip blanks (also 0s)
                and (not l2 or r[tc.WBS_L2] == l2)
                and (not l3 or r[tc.WBS_L3] == l3)
                and (not fund_src or r.get(tc.SOURCE_OF_FUNDS_US_ONLY) == fund_src)
                and (not region or r.get(tc.US_NON_US) == region)
            )
        )

    tc_reader = tc.TableConfigDatabaseClient()

    for l2_cat in tc_reader.get_l2_categories(wbs_l1):

        for l3_cat in tc_reader.get_l3_categories_by_l2(wbs_l1, l2_cat):

            # add US/Non-US
            if with_us_non_us:
                for region in [tc.US, tc.NON_US]:
                    totals.append(
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
            totals.append(
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
        totals.append(
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

    # filter out rows with just 0s
    if only_totals_w_data:
        totals = [r for r in totals if r[tc.GRAND_TOTAL] != 0]

    # Grand Total
    totals.append(
        {
            tc.TOTAL_COL: "GRAND TOTAL",
            tc.NSF_MO_CORE: grab_a_total(fund_src=tc.NSF_MO_CORE),
            tc.NSF_BASE_GRANTS: grab_a_total(fund_src=tc.NSF_BASE_GRANTS),
            tc.US_IN_KIND: grab_a_total(fund_src=tc.US_IN_KIND),
            tc.NON_US_IN_KIND: grab_a_total(fund_src=tc.NON_US_IN_KIND),
            tc.GRAND_TOTAL: grab_a_total(),
        }
    )

    return totals
