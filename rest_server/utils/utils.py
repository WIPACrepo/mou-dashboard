"""Utility functions for the REST server interface."""

from decimal import Decimal
from typing import cast

from ..databases import columns, table_config_db
from . import types
from .mongo_tools import Mongofier


class TableConfigDataAdaptor:
    """Augments a record/table using a `TableConfigDatabaseClient` instance."""

    def __init__(self, tc_db_client: table_config_db.TableConfigDatabaseClient) -> None:
        self.tc_db_client = tc_db_client

    def remove_on_the_fly_fields(self, record: types.Record) -> types.Record:
        """Remove (del) any fields that are only to be calculated on-the-fly."""
        for field in record.copy().keys():
            if field in self.tc_db_client.get_on_the_fly_fields():
                # copy over grand total to FTE
                if (field == columns.GRAND_TOTAL) and (
                    columns.FTE not in record.keys()
                ):
                    record[columns.FTE] = record[field]
                # remove
                del record[field]

        return record

    def add_on_the_fly_fields(self, record: types.Record) -> types.Record:
        """Add fields that are only to be calculated on-the-fly."""
        record = self.remove_on_the_fly_fields(record)

        def _get_fte_subcolumn(record: types.Record) -> str:
            source = record[columns.SOURCE_OF_FUNDS_US_ONLY]
            return cast(str, source)

        # FTE fields
        if columns.FTE in record.keys():
            try:
                record[_get_fte_subcolumn(record)] = record[columns.FTE]
            except KeyError:
                pass
            record[columns.GRAND_TOTAL] = record[columns.FTE]

        # US-only fields
        inst = cast(str, record[columns.INSTITUTION])
        record[columns.US_NON_US] = self.tc_db_client.us_or_non_us(inst)
        if record[columns.US_NON_US] == table_config_db.NON_US:
            record[columns.SOURCE_OF_FUNDS_US_ONLY] = columns.NON_US_IN_KIND

        return record

    def get_total_rows(
        self,
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
                    Decimal(str(r[columns.FTE]))  # avoid floating point loss
                    for r in table
                    if r
                    and columns.TOTAL_COL not in r.keys()  # skip any total rows
                    and r[columns.FTE]  # skip blanks (also 0s)
                    and (not l2 or r[columns.WBS_L2] == l2)
                    and (not l3 or r[columns.WBS_L3] == l3)
                    and (
                        not fund_src
                        or r.get(columns.SOURCE_OF_FUNDS_US_ONLY) == fund_src
                    )
                    and (not region or r.get(columns.US_NON_US) == region)
                )
            )

        for l2_cat in self.tc_db_client.get_l2_categories(wbs_l1):

            for l3_cat in self.tc_db_client.get_l3_categories_by_l2(wbs_l1, l2_cat):

                # add US/Non-US
                if with_us_non_us:
                    for region in [table_config_db.US, table_config_db.NON_US]:
                        totals.append(
                            {
                                columns.WBS_L2: l2_cat,
                                columns.WBS_L3: l3_cat,
                                columns.US_NON_US: region,
                                columns.TOTAL_COL: f"L3 {region} total | {l3_cat}".upper(),
                                columns.NSF_MO_CORE: grab_a_total(
                                    l2=l2_cat,
                                    l3=l3_cat,
                                    fund_src=columns.NSF_MO_CORE,
                                    region=region,
                                ),
                                columns.NSF_BASE_GRANTS: grab_a_total(
                                    l2=l2_cat,
                                    l3=l3_cat,
                                    fund_src=columns.NSF_BASE_GRANTS,
                                    region=region,
                                ),
                                columns.US_IN_KIND: grab_a_total(
                                    l2=l2_cat,
                                    l3=l3_cat,
                                    fund_src=columns.US_IN_KIND,
                                    region=region,  #
                                ),
                                columns.NON_US_IN_KIND: grab_a_total(
                                    l2=l2_cat,
                                    l3=l3_cat,
                                    fund_src=columns.NON_US_IN_KIND,
                                    region=region,
                                ),
                                columns.GRAND_TOTAL: grab_a_total(
                                    l2=l2_cat, l3=l3_cat, region=region
                                ),
                            }
                        )

                # add L3
                totals.append(
                    {
                        columns.WBS_L2: l2_cat,
                        columns.WBS_L3: l3_cat,
                        columns.TOTAL_COL: f"L3 total | {l3_cat}".upper(),
                        columns.NSF_MO_CORE: grab_a_total(
                            l2=l2_cat, l3=l3_cat, fund_src=columns.NSF_MO_CORE
                        ),  # #
                        columns.NSF_BASE_GRANTS: grab_a_total(
                            l2=l2_cat, l3=l3_cat, fund_src=columns.NSF_BASE_GRANTS
                        ),
                        columns.US_IN_KIND: grab_a_total(
                            l2=l2_cat, l3=l3_cat, fund_src=columns.US_IN_KIND
                        ),  # ##
                        columns.NON_US_IN_KIND: grab_a_total(
                            l2=l2_cat, l3=l3_cat, fund_src=columns.NON_US_IN_KIND
                        ),
                        columns.GRAND_TOTAL: grab_a_total(l2=l2_cat, l3=l3_cat),
                    }
                )

            # add L2
            totals.append(
                {
                    columns.WBS_L2: l2_cat,
                    columns.TOTAL_COL: f"L2 total | {l2_cat}".upper(),
                    columns.NSF_MO_CORE: grab_a_total(
                        l2=l2_cat, fund_src=columns.NSF_MO_CORE
                    ),
                    columns.NSF_BASE_GRANTS: grab_a_total(
                        l2=l2_cat, fund_src=columns.NSF_BASE_GRANTS
                    ),
                    columns.US_IN_KIND: grab_a_total(
                        l2=l2_cat, fund_src=columns.US_IN_KIND
                    ),
                    columns.NON_US_IN_KIND: grab_a_total(
                        l2=l2_cat, fund_src=columns.NON_US_IN_KIND
                    ),
                    columns.GRAND_TOTAL: grab_a_total(l2=l2_cat),
                }
            )

        # filter out rows with just 0s
        if only_totals_w_data:
            totals = [r for r in totals if r[columns.GRAND_TOTAL] != 0]

        # Grand Total
        totals.append(
            {
                columns.TOTAL_COL: "GRAND TOTAL",
                columns.NSF_MO_CORE: grab_a_total(fund_src=columns.NSF_MO_CORE),
                columns.NSF_BASE_GRANTS: grab_a_total(fund_src=columns.NSF_BASE_GRANTS),
                columns.US_IN_KIND: grab_a_total(fund_src=columns.US_IN_KIND),
                columns.NON_US_IN_KIND: grab_a_total(fund_src=columns.NON_US_IN_KIND),
                columns.GRAND_TOTAL: grab_a_total(),
            }
        )

        return totals


class MoUDataAdaptor:
    """Augments MoU data using a `TableConfigDatabaseClient` instance."""

    IS_DELETED = "deleted"

    def __init__(self, tc_db_client: table_config_db.TableConfigDatabaseClient) -> None:
        self.tc_db_client = tc_db_client

    def _validate_record_data(self, wbs_db: str, record: types.Record) -> None:
        """Check that each value in a dropdown-type column is valid.

        If not, raise Exception.
        """
        for col_raw, value in record.items():
            col = Mongofier.demongofy_key_name(col_raw)

            # Blanks are okay
            if not value:
                continue

            # Validate a simple dropdown column
            if col in self.tc_db_client.get_simple_dropdown_menus(wbs_db):
                if value in self.tc_db_client.get_simple_dropdown_menus(wbs_db)[col]:
                    continue
                raise Exception(f"Invalid Simple-Dropdown Data: {col=} {record=}")

            # Validate a conditional dropdown column
            if col in self.tc_db_client.get_conditional_dropdown_menus(wbs_db):
                parent_col, menus = self.tc_db_client.get_conditional_dropdown_menus(
                    wbs_db
                )[col]

                # Get parent value
                if parent_col in record:
                    parent_value = record[parent_col]
                # Check mongofied version  # pylint: disable=C0325
                elif (mpc := Mongofier.mongofy_key_name(parent_col)) in record:
                    parent_value = record[mpc]
                # Parent column is missing (*NOT* '' value)
                else:  # validate with any/all parents
                    if value in [v for _, vals in menus.items() for v in vals]:
                        continue
                    raise Exception(
                        f"{menus} Invalid Conditional-Dropdown (Orphan) Data: {col=} {record=}"
                    )

                # validate with parent value
                if parent_value and (value in menus[parent_value]):  # type: ignore[index]
                    continue
                raise Exception(f"Invalid Conditional-Dropdown Data: {col=} {record=}")

    def mongofy_record(
        self,
        wbs_db: str,
        record: types.Record,
        assert_data: bool = True,
    ) -> types.Record:
        """Transform record to mongo-friendly and validate data."""
        # assert data is valid
        if assert_data:
            self._validate_record_data(wbs_db, record)

        record = Mongofier.mongofy_document(record)

        return record

    @staticmethod
    def demongofy_record(record: types.Record) -> types.Record:
        """Transform mongo-friendly record into a usable record."""
        record = Mongofier.demongofy_document(record)

        if MoUDataAdaptor.IS_DELETED in record.keys():
            record.pop(MoUDataAdaptor.IS_DELETED)

        return record
