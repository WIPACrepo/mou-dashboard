"""Utility functions for the REST server interface."""

from decimal import Decimal
from typing import Any, Callable, Dict, cast

from bson.objectid import ObjectId  # type: ignore[import]

from ..databases import table_config_db as tc_db
from . import types


class TableConfigDataAdaptor:
    """Augments a record/table using a `TableConfigDatabaseClient` instance."""

    def __init__(self, tc_db_client: tc_db.TableConfigDatabaseClient) -> None:
        self.tc_db_client = tc_db_client

    def remove_on_the_fly_fields(self, record: types.Record) -> types.Record:
        """Remove (del) any fields that are only to be calculated on-the-fly."""
        for field in record.copy().keys():
            if field in self.tc_db_client.get_on_the_fly_fields():
                # copy over grand total to FTE
                if (field == tc_db.GRAND_TOTAL) and (tc_db.FTE not in record.keys()):
                    record[tc_db.FTE] = record[field]
                # remove
                del record[field]

        return record

    def add_on_the_fly_fields(self, record: types.Record) -> types.Record:
        """Add fields that are only to be calculated on-the-fly."""
        record = self.remove_on_the_fly_fields(record)

        def _get_fte_subcolumn(record: types.Record) -> str:
            source = record[tc_db.SOURCE_OF_FUNDS_US_ONLY]
            return cast(str, source)

        # FTE fields
        if tc_db.FTE in record.keys():
            try:
                record[_get_fte_subcolumn(record)] = record[tc_db.FTE]
            except KeyError:
                pass
            record[tc_db.GRAND_TOTAL] = record[tc_db.FTE]

        # US-only fields
        inst = cast(str, record[tc_db.INSTITUTION])
        record[tc_db.US_NON_US] = self.tc_db_client.us_or_non_us(inst)
        if record[tc_db.US_NON_US] == tc_db.NON_US:
            record[tc_db.SOURCE_OF_FUNDS_US_ONLY] = tc_db.NON_US_IN_KIND

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
                    Decimal(str(r[tc_db.FTE]))  # avoid floating point loss
                    for r in table
                    if r
                    and tc_db.TOTAL_COL not in r.keys()  # skip any total rows
                    and r[tc_db.FTE]  # skip blanks (also 0s)
                    and (not l2 or r[tc_db.WBS_L2] == l2)
                    and (not l3 or r[tc_db.WBS_L3] == l3)
                    and (
                        not fund_src or r.get(tc_db.SOURCE_OF_FUNDS_US_ONLY) == fund_src
                    )
                    and (not region or r.get(tc_db.US_NON_US) == region)
                )
            )

        for l2_cat in self.tc_db_client.get_l2_categories(wbs_l1):

            for l3_cat in self.tc_db_client.get_l3_categories_by_l2(wbs_l1, l2_cat):

                # add US/Non-US
                if with_us_non_us:
                    for region in [tc_db.US, tc_db.NON_US]:
                        totals.append(
                            {
                                tc_db.WBS_L2: l2_cat,
                                tc_db.WBS_L3: l3_cat,
                                tc_db.US_NON_US: region,
                                tc_db.TOTAL_COL: f"L3 {region} total | {l3_cat}".upper(),
                                tc_db.NSF_MO_CORE: grab_a_total(
                                    l2=l2_cat,
                                    l3=l3_cat,
                                    fund_src=tc_db.NSF_MO_CORE,
                                    region=region,
                                ),
                                tc_db.NSF_BASE_GRANTS: grab_a_total(
                                    l2=l2_cat,
                                    l3=l3_cat,
                                    fund_src=tc_db.NSF_BASE_GRANTS,
                                    region=region,
                                ),
                                tc_db.US_IN_KIND: grab_a_total(
                                    l2=l2_cat,
                                    l3=l3_cat,
                                    fund_src=tc_db.US_IN_KIND,
                                    region=region,  #
                                ),
                                tc_db.NON_US_IN_KIND: grab_a_total(
                                    l2=l2_cat,
                                    l3=l3_cat,
                                    fund_src=tc_db.NON_US_IN_KIND,
                                    region=region,
                                ),
                                tc_db.GRAND_TOTAL: grab_a_total(
                                    l2=l2_cat, l3=l3_cat, region=region
                                ),
                            }
                        )

                # add L3
                totals.append(
                    {
                        tc_db.WBS_L2: l2_cat,
                        tc_db.WBS_L3: l3_cat,
                        tc_db.TOTAL_COL: f"L3 total | {l3_cat}".upper(),
                        tc_db.NSF_MO_CORE: grab_a_total(
                            l2=l2_cat, l3=l3_cat, fund_src=tc_db.NSF_MO_CORE
                        ),  # #
                        tc_db.NSF_BASE_GRANTS: grab_a_total(
                            l2=l2_cat, l3=l3_cat, fund_src=tc_db.NSF_BASE_GRANTS
                        ),
                        tc_db.US_IN_KIND: grab_a_total(
                            l2=l2_cat, l3=l3_cat, fund_src=tc_db.US_IN_KIND
                        ),  # ##
                        tc_db.NON_US_IN_KIND: grab_a_total(
                            l2=l2_cat, l3=l3_cat, fund_src=tc_db.NON_US_IN_KIND
                        ),
                        tc_db.GRAND_TOTAL: grab_a_total(l2=l2_cat, l3=l3_cat),
                    }
                )

            # add L2
            totals.append(
                {
                    tc_db.WBS_L2: l2_cat,
                    tc_db.TOTAL_COL: f"L2 total | {l2_cat}".upper(),
                    tc_db.NSF_MO_CORE: grab_a_total(
                        l2=l2_cat, fund_src=tc_db.NSF_MO_CORE
                    ),
                    tc_db.NSF_BASE_GRANTS: grab_a_total(
                        l2=l2_cat, fund_src=tc_db.NSF_BASE_GRANTS
                    ),
                    tc_db.US_IN_KIND: grab_a_total(
                        l2=l2_cat, fund_src=tc_db.US_IN_KIND
                    ),
                    tc_db.NON_US_IN_KIND: grab_a_total(
                        l2=l2_cat, fund_src=tc_db.NON_US_IN_KIND
                    ),
                    tc_db.GRAND_TOTAL: grab_a_total(l2=l2_cat),
                }
            )

        # filter out rows with just 0s
        if only_totals_w_data:
            totals = [r for r in totals if r[tc_db.GRAND_TOTAL] != 0]

        # Grand Total
        totals.append(
            {
                tc_db.TOTAL_COL: "GRAND TOTAL",
                tc_db.NSF_MO_CORE: grab_a_total(fund_src=tc_db.NSF_MO_CORE),
                tc_db.NSF_BASE_GRANTS: grab_a_total(fund_src=tc_db.NSF_BASE_GRANTS),
                tc_db.US_IN_KIND: grab_a_total(fund_src=tc_db.US_IN_KIND),
                tc_db.NON_US_IN_KIND: grab_a_total(fund_src=tc_db.NON_US_IN_KIND),
                tc_db.GRAND_TOTAL: grab_a_total(),
            }
        )

        return totals


class Mongofier:
    """Tools for moving/transforming data in/out of a MongoDB."""

    @staticmethod
    def mongofy_key_name(key: str) -> str:
        """Transform string to mongo-friendly."""
        return key.replace(".", ";")

    @staticmethod
    def demongofy_key_name(key: str) -> str:
        """Transform string from mongo-friendly to human-friendly."""
        return key.replace(";", ".")

    @staticmethod
    def mongofy_every_key(dicto: Dict[str, Any]) -> Dict[str, Any]:
        """Transform all keys to mongo-friendly, recursively."""
        return Mongofier._transform_every_key(dicto, Mongofier.mongofy_key_name)

    @staticmethod
    def demongofy_every_key(dicto: Dict[str, Any]) -> Dict[str, Any]:
        """Transform all keys to human-friendly, recursively."""
        return Mongofier._transform_every_key(dicto, Mongofier.demongofy_key_name)

    @staticmethod
    def _transform_every_key(
        dicto: Dict[str, Any], key_func: Callable[[str], str]
    ) -> Dict[str, Any]:
        # first get the keys right
        for key in list(dicto.keys()):
            dicto[key_func(key)] = dicto.pop(key)

        # then get any nested dicts
        for key, val in list(dicto.items()):
            if isinstance(val, dict):
                dicto[key] = Mongofier._transform_every_key(val, key_func)

        return dicto


class MoUDataAdaptor:
    """Augments MoU data using a `TableConfigDatabaseClient` instance."""

    IS_DELETED = "deleted"

    def __init__(self, tc_db_client: tc_db.TableConfigDatabaseClient) -> None:
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

        # mongofy key names
        record = Mongofier.mongofy_every_key(record)

        # cast ID
        if record.get(tc_db.ID):
            record[tc_db.ID] = ObjectId(record[tc_db.ID])

        return record

    @staticmethod
    def demongofy_record(record: types.Record) -> types.Record:
        """Transform mongo-friendly record into a usable record."""
        # replace Nones with ""
        for key in record.keys():
            if record[key] is None:
                record[key] = ""

        # demongofy key names
        for key in list(record.keys()):
            record[MoUDataAdaptor.demongofy_key_name(key)] = record.pop(key)

        record[tc_db.ID] = str(record[tc_db.ID])  # cast ID

        if MoUDataAdaptor.IS_DELETED in record.keys():
            record.pop(MoUDataAdaptor.IS_DELETED)

        return record
