"""Unit test rest_server module."""

# pylint: disable=W0212


import copy
import pprint
import sys
from decimal import Decimal
from typing import Any, Final, List
from unittest.mock import ANY, AsyncMock, Mock, patch, sentinel

import nest_asyncio  # type: ignore[import]
import pytest
from bson.objectid import ObjectId  # type: ignore[import]

from . import data

sys.path.append(".")
from rest_server.utils import (  # isort:skip  # noqa # pylint: disable=E0401,C0413,C0411
    utils,
    types,
)
from rest_server.databases import (  # isort:skip  # noqa # pylint: disable=E0401,C0413,C0411
    mou_db,
    table_config_db as tc_db,
)
from rest_server import config  # isort:skip  # noqa # pylint: disable=E0401,C0413,C0411


nest_asyncio.apply()  # allows nested event loops


MOU_DB_CLIENT: Final = "rest_server.databases.mou_db.MoUDatabaseClient"
MOTOR_CLIENT: Final = "motor.motor_tornado.MotorClient"
TC_DB_CLIENT: Final = "rest_server.databases.table_config_db.TableConfigDatabaseClient"
WBS: Final = "mo"


def reset_mock(*args: Mock) -> None:
    """Reset all the Mock objects given."""
    for a in args:  # pylint: disable=C0103
        a.reset_mock()


@pytest.fixture
def mock_mongo(mocker: Any) -> Any:
    """Patch mock_mongo."""
    mock_mongo = mocker.patch(MOTOR_CLIENT)  # pylint:disable=redefined-outer-name
    mock_mongo.list_database_names.side_effect = AsyncMock()
    return mock_mongo


class TestDBUtils:  # pylint: disable=R0904
    """Test private methods in mou_db.py."""

    @staticmethod
    @patch(MOU_DB_CLIENT + "._ensure_all_db_indexes")
    def test_init(mock_eadi: Any) -> None:
        """Test MoUDatabaseClient.__init__()."""
        # Call
        moumc = mou_db.MoUDatabaseClient(sentinel._client)

        # Assert
        assert moumc._client == sentinel._client
        mock_eadi.assert_called()

        # --- test w/ xlsx
        # Mock
        reset_mock(mock_eadi)

        # Call
        moumc = mou_db.MoUDatabaseClient(sentinel._client)

        # Assert
        assert moumc._client == sentinel._client
        mock_eadi.assert_called()

    @staticmethod
    @patch(TC_DB_CLIENT + ".get_conditional_dropdown_menus")
    @patch(TC_DB_CLIENT + ".get_simple_dropdown_menus")
    def test_validate_record_data(mock_gsdm: Any, mock_gcdm: Any) -> None:
        """Test _validate_record_data()."""
        mock_gsdm.return_value = {
            "F.o.o": ["foo-1", "foo-2"],
            "B.a.r": ["bar-1", "bar-2", "bar-3"],
            "Baz": [],
        }

        mock_gcdm.return_value = {
            "Ham": (
                "F.o.o",
                {
                    "foo-1": ["1A-I", "1A-II"],
                    "foo-2": ["1B-I", "1B-II", "1B-III", "1B-IV"],
                },
            ),
            "Eggs": (
                "B.a.r",
                {
                    "bar-1": ["2A-I", "2A-II", "2A-III", "2A-IV", "2A-V", "2A-VI"],
                    "bar-2": [],
                },
            ),
        }

        # Test good records
        good_records: List[types.Record] = [
            {
                "F.o.o": "foo-2",
                "B.a.r": "bar-1",
                "Baz": "",
                "Ham": "1B-III",
                "Eggs": "2A-IV",
            },  # full record
            {
                "F;o;o": "foo-2",
                "B;a;r": "bar-1",
                "Baz": "",
                "Ham": "1B-III",
                "Eggs": "2A-IV",
            },  # mongofied & full record
            {
                "F.o.o": "foo-2",
                "B.a.r": "bar-2",
                "Ham": "1B-III",
                "Eggs": "",
            },  # missing columns
            {
                "F.o.o": "foo-2",
                "B.a.r": "bar-2",
                "Ham": "",
                "Eggs": "",
            },  # blank values & missing columns
            {
                "F.o.o": "foo-2",
                "B.a.r": "",
                "Ham": "",
                "Eggs": "",
            },  # blank values & missing columns
            {"F;o;o": "foo-2"},  # mongofied & missing columns
            {"F;o;o": ""},  # mongofied & blank values & missing columns
            {"Ham": "1B-III"},  # missing conditional-parent column
            {},  # no columns
        ]

        for record in good_records:
            mou_db.MoUDatabaseClient._validate_record_data(WBS, record)

        # Test bad records
        bad_records: List[types.Record] = [
            {"F.o.o": "foo-2", "Ham": 357},  # bad conditional column
            {
                "F.o.o": "pork",
                "Ham": "1B-III",
            },  # bad simple (conditional-parent) column
            {
                "F;o;o": "foo-2",
                "B;a;r": "bar-2",
                "Ham": "1B-III",
                "Eggs": "spam",
            },  # bad conditional column
            {"Baz": "beef"},  # bad simple column
            {"F.o.o": "", "Ham": "1B-III"},  # bad conditional column w/ blank parent
        ]

        for record in bad_records:
            with pytest.raises(Exception):
                mou_db.MoUDatabaseClient._validate_record_data(WBS, record)

    @staticmethod
    def test_mongofy_key_name() -> None:
        """Test _mongofy_key_name()."""
        # Set-Up
        keys = ["", "...", " ", "N;M"]
        mongofied_keys = ["", ";;;", " ", "N;M"]

        # Call & Assert
        for key, mkey in zip(keys, mongofied_keys):
            assert mou_db.MoUDatabaseClient._mongofy_key_name(key) == mkey

    @staticmethod
    def test_demongofy_key_name() -> None:
        """Test _demongofy_key_name()."""
        # Set-Up
        keys = ["", ";;;", " ", "A;C", "."]
        demongofied_keys = ["", "...", " ", "A.C", "."]

        # Call & Assert
        for key, dkey in zip(keys, demongofied_keys):
            assert mou_db.MoUDatabaseClient._demongofy_key_name(key) == dkey

    @staticmethod
    @patch(MOU_DB_CLIENT + "._validate_record_data")
    def test_mongofy_record(mock_vrd: Any) -> None:
        """Test _mongofy_record()."""
        # Set-Up
        records: List[types.Record] = [
            {},
            {"a.b": 5, "Foo;Bar": "Baz"},
            {"_id": "5f725c6af0803660075769ab", "FOO": "bar"},
        ]

        mongofied_records: List[types.Record] = [
            {},
            {"a;b": 5, "Foo;Bar": "Baz"},
            {"_id": ObjectId("5f725c6af0803660075769ab"), "FOO": "bar"},
        ]
        mock_vrd.side_effect = None

        # Call & Assert
        for record, mrecord in zip(records, mongofied_records):
            assert mou_db.MoUDatabaseClient._mongofy_record(WBS, record) == mrecord

    @staticmethod
    def test_demongofy_record() -> None:
        """Test _demongofy_record()."""
        # Set-Up
        records: List[types.Record] = [
            {"_id": ANY},
            {"_id": ANY, mou_db.IS_DELETED: True},
            {"_id": ANY, mou_db.IS_DELETED: False},
            {"_id": ANY, "a;b": 5, "Foo;Bar": "Baz"},
            {"_id": ObjectId("5f725c6af0803660075769ab"), "FOO": "bar"},
        ]

        demongofied_records: List[types.Record] = [
            {"_id": ANY},
            {"_id": ANY},
            {"_id": ANY},
            {"_id": ANY, "a.b": 5, "Foo.Bar": "Baz"},
            {"_id": "5f725c6af0803660075769ab", "FOO": "bar"},
        ]

        # Call & Assert
        for record, drecord in zip(records, demongofied_records):
            assert mou_db.MoUDatabaseClient._demongofy_record(record) == drecord

        # Error Case
        with pytest.raises(KeyError):
            mou_db.MoUDatabaseClient._demongofy_record({"a;b": 5, "Foo;Bar": "Baz"})

    @staticmethod
    @pytest.mark.asyncio  # type: ignore[misc]
    async def test_list_database_names(mock_mongo: Any) -> None:
        """Test _list_database_names()."""
        # Mock
        dbs = ["foo", "bar", "baz"] + config.EXCLUDE_DBS[:3]
        moumc = mou_db.MoUDatabaseClient(mock_mongo)
        mock_mongo.list_database_names.side_effect = AsyncMock(return_value=dbs)

        # Call
        ret = await moumc._list_database_names()

        # Assert
        assert ret == dbs[:3]
        assert mock_mongo.list_database_names.side_effect.await_count == 1

    # NOTE: public methods are tested in integration tests


class TestUtils:
    """Test utils.py."""

    @staticmethod
    def test_remove_on_the_fly_fields() -> None:
        """Test remove_on_the_fly_fields()."""
        # Set-Up
        before_records: List[types.Record] = [
            {"_id": ANY},
            {"Grand Total": 999.99, "FTE": 50},
            {"NSF M&O Core": 100},
            {"_id": ANY, "a;b": 5, "Foo;Bar": "Baz", "Grand Total": 999.99},
        ]
        after_records: List[types.Record] = [
            {"_id": ANY},
            {"FTE": 50},
            {},
            {"_id": ANY, "a;b": 5, "Foo;Bar": "Baz", "FTE": 999.99},
        ]

        # Call & Assert
        for before, after in zip(before_records, after_records):
            assert utils.remove_on_the_fly_fields(before) == after
            assert utils.remove_on_the_fly_fields(after) == after

    @staticmethod
    def test_add_on_the_fly_fields() -> None:
        """Test add_on_the_fly_fields()."""
        # Set-Up
        before_records: List[types.Record] = [
            {
                "_id": ANY,
                "Institution": "SBU",
                "Source of Funds (U.S. Only)": "NSF M&O Core",
            },
            {
                "Institution": "SKKU",
                "US / Non-US": "BLAH",  # will get overwritten
                "Source of Funds (U.S. Only)": "Non-US In-Kind",
                "Grand Total": 50,  # will get copied to FTE
            },
            {
                "Institution": "MERCER",
                "Source of Funds (U.S. Only)": "NSF Base Grants",
                "FTE": 100,
                "NSF Base Grants": 5555555555,  # will get overwritten w/ FTE
            },
            {
                "_id": ANY,
                "a;b": 5,
                "Foo;Bar": "Baz",
                "Institution": "UW",
                "Source of Funds (U.S. Only)": "US In-Kind",
                "FTE": 999.99,
                "Grand Total": 5555555555,  # will get overwritten w/ FTE
            },
        ]
        after_records: List[types.Record] = [
            {
                "_id": ANY,
                "Institution": "SBU",
                "US / Non-US": "US",
                "Source of Funds (U.S. Only)": "NSF M&O Core",
            },
            {
                "Institution": "SKKU",
                "US / Non-US": "Non-US",
                "Source of Funds (U.S. Only)": "Non-US In-Kind",
                "FTE": 50,
                "Non-US In-Kind": 50,
                "Grand Total": 50,
            },
            {
                "Institution": "MERCER",
                "US / Non-US": "US",
                "Source of Funds (U.S. Only)": "NSF Base Grants",
                "FTE": 100,
                "NSF Base Grants": 100,
                "Grand Total": 100,
            },
            {
                "_id": ANY,
                "a;b": 5,
                "Foo;Bar": "Baz",
                "Institution": "UW",
                "US / Non-US": "US",
                "Source of Funds (U.S. Only)": "US In-Kind",
                "FTE": 999.99,
                "US In-Kind": 999.99,
                "Grand Total": 999.99,
            },
        ]

        # Call & Assert
        for before, after in zip(before_records, after_records):
            assert utils.add_on_the_fly_fields(before) == after
            assert utils.add_on_the_fly_fields(after) == after

        # Error Case
        with pytest.raises(KeyError):
            # require institution
            _ = utils.add_on_the_fly_fields({"foo": "bar", "FTE": 0})
        # with pytest.raises(KeyError): NOTE - removed b/c Upgrade doesn't require "Source of Funds"
        #     _ = utils.add_on_the_fly_fields(
        #         {"foo": "bar", "FTE": 0, "Institution": "UW"}
        #     )
        _ = utils.add_on_the_fly_fields({"foo": "bar", "Institution": "SUNY"})
        with pytest.raises(KeyError):
            # require institution
            _ = utils.add_on_the_fly_fields(
                {
                    "foo": "bar",
                    "FTE": 0,
                    "Source of Funds (U.S. Only)": "NSF Base Grants",
                }
            )

    @staticmethod
    def test_insert_total_rows(mock_mongo: Any) -> None:
        """Test insert_total_rows().

        No need to integration test this.
        """
        tc_db_client = tc_db.TableConfigDatabaseClient(mock_mongo)

        def _assert_funds_totals(_rows: types.Table, _total_row: types.Record) -> None:
            print("\n-----------------------------------------------------\n")
            pprint.pprint(_rows)
            pprint.pprint(_total_row)
            assert _total_row[tc_db.GRAND_TOTAL] == float(
                sum(Decimal(str(r[tc_db.FTE])) for r in _rows)
            )
            for fund in [
                tc_db.NSF_MO_CORE,
                tc_db.NSF_BASE_GRANTS,
                tc_db.US_IN_KIND,
                tc_db.NON_US_IN_KIND,
            ]:
                assert _total_row[fund] == float(
                    sum(
                        Decimal(str(r[tc_db.FTE]))
                        for r in _rows
                        if r[tc_db.SOURCE_OF_FUNDS_US_ONLY] == fund
                    )
                )

        # Test example table and empty table
        test_tables: Final[List[types.Table]] = [copy.deepcopy(data.FTE_ROWS), []]
        for table in test_tables:
            # Call
            totals = utils.get_total_rows(WBS, table)
            # pprint.pprint(totals)

            # Assert total sums
            for total_row in totals:

                # L3 US/Non-US Level
                if (
                    "L3 NON-US TOTAL"
                    in total_row[tc_db.TOTAL_COL]  # type: ignore[operator]
                    or "L3 US TOTAL"
                    in total_row[tc_db.TOTAL_COL]  # type: ignore[operator]
                ):
                    _assert_funds_totals(
                        [
                            r
                            for r in table
                            if total_row[tc_db.WBS_L2] == r[tc_db.WBS_L2]
                            and total_row[tc_db.WBS_L3] == r[tc_db.WBS_L3]
                            and total_row[tc_db.US_NON_US] == r[tc_db.US_NON_US]
                        ],
                        total_row,
                    )

                # L3 Level
                elif "L3 TOTAL" in total_row[tc_db.TOTAL_COL]:  # type: ignore[operator]
                    _assert_funds_totals(
                        [
                            r
                            for r in table
                            if total_row[tc_db.WBS_L2] == r[tc_db.WBS_L2]
                            and total_row[tc_db.WBS_L3] == r[tc_db.WBS_L3]
                        ],
                        total_row,
                    )

                # L2 Level
                elif "L2 TOTAL" in total_row[tc_db.TOTAL_COL]:  # type: ignore[operator]
                    _assert_funds_totals(
                        [
                            r
                            for r in table
                            if total_row[tc_db.WBS_L2] == r[tc_db.WBS_L2]
                        ],
                        total_row,
                    )

                # Grand Total
                elif (
                    "GRAND TOTAL"
                    in total_row[tc_db.TOTAL_COL]  # type: ignore[operator]
                ):
                    _assert_funds_totals(table, total_row)

                # Other Kind?
                else:
                    raise Exception(f"Unaccounted total row ({total_row}).")

            # Assert that every possible total is there (including rows with only 0s)
            for l2_cat in tc_db_client.get_l2_categories(WBS):
                assert l2_cat in set(r.get(tc_db.WBS_L2) for r in totals)
                for l3_cat in tc_db_client.get_l3_categories_by_l2(WBS, l2_cat):
                    assert l3_cat in set(r.get(tc_db.WBS_L3) for r in totals)


class TestTableConfig:
    """Test table_config.py."""

    @staticmethod
    def test_us_or_non_us(mock_mongo: Any) -> None:
        """Test _us_or_non_us().

        Function is very simple, so also test institution-dict's format.
        """
        tc_db_client = tc_db.TableConfigDatabaseClient(mock_mongo)

        for inst in tc_db_client.institution_dicts.values():
            assert "abbreviation" in inst
            assert "is_US" in inst
            assert inst["is_US"] is True or inst["is_US"] is False
            if inst["is_US"]:
                assert tc_db_client.us_or_non_us(inst["abbreviation"]) == "US"
            else:
                assert tc_db_client.us_or_non_us(inst["abbreviation"]) == "Non-US"
