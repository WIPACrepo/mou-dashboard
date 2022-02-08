"""Unit test rest_server module."""

# pylint: disable=W0212,redefined-outer-name


import copy
import pprint
import sys
import time
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
    mongo_tools,
)
from rest_server.databases import (  # isort:skip  # noqa # pylint: disable=E0401,C0413,C0411
    mou_db,
    table_config_db,
    columns,
)
from rest_server import config  # isort:skip  # noqa # pylint: disable=E0401,C0413,C0411


nest_asyncio.apply()  # allows nested event loops


MOU_DB_CLIENT: Final = "rest_server.databases.mou_db.MoUDatabaseClient"
MOTOR_CLIENT: Final = "motor.motor_tornado.MotorClient"
TC_DB_CLIENT: Final = "rest_server.databases.table_config_db.TableConfigDatabaseClient"
MOU_DATA_ADAPTOR: Final = "rest_server.utils.utils.MoUDataAdaptor"
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


class TestMoUDB:  # pylint: disable=R0904
    """Test private methods in mou_db.py."""

    @staticmethod
    @patch(MOU_DB_CLIENT + "._ensure_all_db_indexes")
    @patch(TC_DB_CLIENT + ".get_most_recent_doc")
    @patch(TC_DB_CLIENT + "._insert_replace")
    def test_init(mock_ir: Any, mock_gmrd: Any, mock_eadi: Any) -> None:
        """Test MoUDatabaseClient.__init__()."""
        # Setup & Mock
        mock_gmrd.side_effect = mongo_tools.DocumentNotFoundError()  # "db is empty"
        mock_ir.return_value = None  # no-op the db insert

        # Call
        mou_db_client = mou_db.MoUDatabaseClient(
            sentinel.mongo,
            utils.MoUDataAdaptor(
                table_config_db.TableConfigDatabaseClient(sentinel.tc_mongo)
            ),
        )

        # Assert
        assert mou_db_client._mongo == sentinel.mongo

        # --- test w/ xlsx
        # Mock
        reset_mock(mock_eadi)

        # Call
        mou_db_client = mou_db.MoUDatabaseClient(
            sentinel.mongo,
            utils.MoUDataAdaptor(
                table_config_db.TableConfigDatabaseClient(sentinel.tc_mongo)
            ),
        )

        # Assert
        assert mou_db_client._mongo == sentinel.mongo

    @staticmethod
    @pytest.mark.asyncio  # type: ignore[misc]
    @patch(TC_DB_CLIENT + ".get_most_recent_doc")
    @patch(TC_DB_CLIENT + "._insert_replace")
    async def test_list_database_names(
        mock_ir: Any, mock_gmrd: Any, mock_mongo: Any
    ) -> None:
        """Test _list_database_names()."""
        # Setup & Mock
        dbs = ["foo", "bar", "baz"] + config.EXCLUDE_DBS[:3]
        mock_gmrd.side_effect = mongo_tools.DocumentNotFoundError()  # "db is empty"
        mock_ir.return_value = None  # no-op the db insert
        mou_db_client = mou_db.MoUDatabaseClient(
            mock_mongo,
            utils.MoUDataAdaptor(
                table_config_db.TableConfigDatabaseClient(sentinel.tc_mongo)
            ),
        )
        mock_mongo.list_database_names.side_effect = AsyncMock(return_value=dbs)

        # Call
        ret = await mou_db_client._list_database_names()

        # Assert
        assert ret == dbs[:3]
        assert mock_mongo.list_database_names.side_effect.await_count == 1

    # NOTE: public methods are tested in integration tests


class TestMongofier:
    """Test mongo_tools.Mongofier."""

    @staticmethod
    def test_mongofy_key_name() -> None:
        """Test _mongofy_key_name()."""
        # Set-Up
        keys = ["", "...", " ", "N;M"]
        mongofied_keys = ["", ";;;", " ", "N;M"]

        # Call & Assert
        for key, mkey in zip(keys, mongofied_keys):
            assert mongo_tools.Mongofier.mongofy_key_name(key) == mkey

    @staticmethod
    def test_demongofy_key_name() -> None:
        """Test demongofy_key_name()."""
        # Set-Up
        keys = ["", ";;;", " ", "A;C", "."]
        demongofied_keys = ["", "...", " ", "A.C", "."]

        # Call & Assert
        for key, dkey in zip(keys, demongofied_keys):
            assert mongo_tools.Mongofier.demongofy_key_name(key) == dkey

    @staticmethod
    def test_mongofy_every_key() -> None:
        """Test _mongofy_every_key() & _demongofy_every_key()."""
        # Set-Up
        dict_in = {
            "": 1,
            "...": 2,
            " ": {"A.B": 33, "NESTED.": {"2x NESTED": 333}},
            "N.M": 4,
        }
        dict_out = {
            "": 1,
            ";;;": 2,
            " ": {"A;B": 33, "NESTED;": {"2x NESTED": 333}},
            "N;M": 4,
        }

        # Calls & Asserts
        into = copy.deepcopy(dict_out)
        assert mongo_tools.Mongofier._mongofy_every_key(into) == dict_out
        assert into == dict_out  # assert in-place change

        into = copy.deepcopy(dict_in)
        assert mongo_tools.Mongofier._mongofy_every_key(into) == dict_out
        assert into == dict_out  # assert in-place change

        into = copy.deepcopy(dict_out)
        assert mongo_tools.Mongofier._demongofy_every_key(into) == dict_in
        assert into == dict_in  # assert in-place change

        into = copy.deepcopy(dict_in)
        assert mongo_tools.Mongofier._demongofy_every_key(dict_in) == dict_in
        assert into == dict_in  # assert in-place change

    @staticmethod
    def test_mongofy_document() -> None:
        """Test mongofy_document() & demongofy_document()."""
        # Set-Up
        original_human = {
            "": "",
            " ": {"xyz": 33, "NESTED.": {"2x NESTED": None}},
            columns.ID: "0123456789ab0123456789ab",
        }
        mongoed = {
            "": "",
            " ": {"xyz": 33, "NESTED;": {"2x NESTED": None}},
            columns.ID: ObjectId("0123456789ab0123456789ab"),
        }
        rehumaned = {
            "": "",
            " ": {"xyz": 33, "NESTED.": {"2x NESTED": ""}},
            columns.ID: "0123456789ab0123456789ab",
        }

        # Calls & Asserts
        into = copy.deepcopy(original_human)
        assert mongo_tools.Mongofier.mongofy_document(into) == mongoed
        assert into != mongoed  # assert in-place change

        into = copy.deepcopy(mongoed)
        assert mongo_tools.Mongofier.demongofy_document(into) == rehumaned
        assert into != rehumaned  # assert in-place change


class TestMoUDataAdaptor:
    """Test utils.MoUDataAdaptor."""

    @staticmethod
    @patch(TC_DB_CLIENT + ".get_conditional_dropdown_menus")
    @patch(TC_DB_CLIENT + ".get_simple_dropdown_menus")
    @patch(TC_DB_CLIENT + ".get_most_recent_doc")
    @patch(TC_DB_CLIENT + "._insert_replace")
    def test_validate_record_data(
        mock_ir: Any, mock_gmrd: Any, mock_gsdm: Any, mock_gcdm: Any
    ) -> None:
        """Test _validate_record_data()."""
        # Setup & Mock
        mock_gmrd.side_effect = mongo_tools.DocumentNotFoundError()  # "db is empty"
        mou_data_adaptor = utils.MoUDataAdaptor(
            table_config_db.TableConfigDatabaseClient(sentinel.mongo)
        )
        mock_ir.return_value = None  # no-op the db insert

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
            mou_data_adaptor._validate_record_data(WBS, record)

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
                mou_data_adaptor._validate_record_data(WBS, record)

    @staticmethod
    @patch(MOU_DATA_ADAPTOR + "._validate_record_data")
    @patch(TC_DB_CLIENT + ".get_most_recent_doc")
    @patch(TC_DB_CLIENT + "._insert_replace")
    def test_mongofy_record(mock_ir: Any, mock_gmrd: Any, mock_vrd: Any) -> None:
        """Test _mongofy_record()."""
        # Setup & Mock
        mock_gmrd.side_effect = mongo_tools.DocumentNotFoundError()  # "db is empty"
        mou_data_adaptor = utils.MoUDataAdaptor(
            table_config_db.TableConfigDatabaseClient(sentinel.mongo)
        )
        mock_ir.return_value = None  # no-op the db insert

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
            assert mou_data_adaptor.mongofy_record(WBS, record) == mrecord

    @staticmethod
    def test_demongofy_record() -> None:
        """Test _demongofy_record()."""
        # Set-Up
        records: List[types.Record] = [
            {"_id": ANY},
            {"_id": ANY, utils.MoUDataAdaptor.IS_DELETED: True},
            {"_id": ANY, utils.MoUDataAdaptor.IS_DELETED: False},
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
            assert utils.MoUDataAdaptor.demongofy_record(record) == drecord

        # Error Case
        with pytest.raises(KeyError):
            utils.MoUDataAdaptor.demongofy_record({"a;b": 5, "Foo;Bar": "Baz"})


class TestTableConfigDataAdaptor:
    """Test utils.TableConfigDataAdaptor."""

    @staticmethod
    @patch(TC_DB_CLIENT + ".get_most_recent_doc")
    @patch(TC_DB_CLIENT + "._insert_replace")
    def test_remove_on_the_fly_fields(mock_ir: Any, mock_gmrd: Any) -> None:
        """Test remove_on_the_fly_fields()."""
        # Setup & Mock
        mock_gmrd.side_effect = mongo_tools.DocumentNotFoundError()  # "db is empty"
        tc_data_adaptor = utils.TableConfigDataAdaptor(
            table_config_db.TableConfigDatabaseClient(sentinel.mongo)
        )
        mock_ir.return_value = None  # no-op the db insert

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
            assert tc_data_adaptor.remove_on_the_fly_fields(before) == after
            assert tc_data_adaptor.remove_on_the_fly_fields(after) == after

    @staticmethod
    @patch(TC_DB_CLIENT + ".get_most_recent_doc")
    @patch(TC_DB_CLIENT + "._insert_replace")
    def test_add_on_the_fly_fields(mock_ir: Any, mock_gmrd: Any) -> None:
        """Test add_on_the_fly_fields()."""
        # Setup & Mock
        mock_gmrd.side_effect = mongo_tools.DocumentNotFoundError()  # "db is empty"
        tc_data_adaptor = utils.TableConfigDataAdaptor(
            table_config_db.TableConfigDatabaseClient(sentinel.mongo)
        )
        mock_ir.return_value = None  # no-op the db insert

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
            assert tc_data_adaptor.add_on_the_fly_fields(before) == after
            assert tc_data_adaptor.add_on_the_fly_fields(after) == after

        # Error Case
        with pytest.raises(KeyError):
            # require institution
            _ = tc_data_adaptor.add_on_the_fly_fields({"foo": "bar", "FTE": 0})
        # with pytest.raises(KeyError): NOTE - removed b/c Upgrade doesn't require "Source of Funds"
        #     _ = utils.add_on_the_fly_fields(
        #         {"foo": "bar", "FTE": 0, "Institution": "UW"}
        #     )
        _ = tc_data_adaptor.add_on_the_fly_fields({"foo": "bar", "Institution": "SUNY"})
        with pytest.raises(KeyError):
            # require institution
            _ = tc_data_adaptor.add_on_the_fly_fields(
                {
                    "foo": "bar",
                    "FTE": 0,
                    "Source of Funds (U.S. Only)": "NSF Base Grants",
                }
            )

    @staticmethod
    @patch(TC_DB_CLIENT + ".get_most_recent_doc")
    @patch(TC_DB_CLIENT + "._insert_replace")
    def test_insert_total_rows(mock_ir: Any, mock_gmrd: Any) -> None:
        """Test insert_total_rows().

        No need to integration test this.
        """
        # Setup & Mock
        mock_gmrd.side_effect = mongo_tools.DocumentNotFoundError()  # "db is empty"
        tc_db_client = table_config_db.TableConfigDatabaseClient(sentinel.mongo)
        mock_ir.return_value = None  # no-op the db insert
        tc_data_adaptor = utils.TableConfigDataAdaptor(tc_db_client)

        def _assert_funds_totals(_rows: types.Table, _total_row: types.Record) -> None:
            print("\n-----------------------------------------------------\n")
            pprint.pprint(_rows)
            pprint.pprint(_total_row)
            assert _total_row[columns.GRAND_TOTAL] == float(
                sum(Decimal(str(r[columns.FTE])) for r in _rows)
            )
            for fund in [
                columns.NSF_MO_CORE,
                columns.NSF_BASE_GRANTS,
                columns.US_IN_KIND,
                columns.NON_US_IN_KIND,
            ]:
                assert _total_row[fund] == float(
                    sum(
                        Decimal(str(r[columns.FTE]))
                        for r in _rows
                        if r[columns.SOURCE_OF_FUNDS_US_ONLY] == fund
                    )
                )

        # Test example table and empty table
        test_tables: Final[List[types.Table]] = [copy.deepcopy(data.FTE_ROWS), []]
        for table in test_tables:
            # Call
            totals = tc_data_adaptor.get_total_rows(WBS, table)
            # pprint.pprint(totals)

            # Assert total sums
            for total_row in totals:

                # L3 US/Non-US Level
                if (
                    "L3 NON-US TOTAL"
                    in total_row[columns.TOTAL_COL]  # type: ignore[operator]
                    or "L3 US TOTAL"
                    in total_row[columns.TOTAL_COL]  # type: ignore[operator]
                ):
                    _assert_funds_totals(
                        [
                            r
                            for r in table
                            if total_row[columns.WBS_L2] == r[columns.WBS_L2]
                            and total_row[columns.WBS_L3] == r[columns.WBS_L3]
                            and total_row[columns.US_NON_US] == r[columns.US_NON_US]
                        ],
                        total_row,
                    )

                # L3 Level
                elif "L3 TOTAL" in total_row[columns.TOTAL_COL]:  # type: ignore[operator]
                    _assert_funds_totals(
                        [
                            r
                            for r in table
                            if total_row[columns.WBS_L2] == r[columns.WBS_L2]
                            and total_row[columns.WBS_L3] == r[columns.WBS_L3]
                        ],
                        total_row,
                    )

                # L2 Level
                elif "L2 TOTAL" in total_row[columns.TOTAL_COL]:  # type: ignore[operator]
                    _assert_funds_totals(
                        [
                            r
                            for r in table
                            if total_row[columns.WBS_L2] == r[columns.WBS_L2]
                        ],
                        total_row,
                    )

                # Grand Total
                elif (
                    "GRAND TOTAL"
                    in total_row[columns.TOTAL_COL]  # type: ignore[operator]
                ):
                    _assert_funds_totals(table, total_row)

                # Other Kind?
                else:
                    raise Exception(f"Unaccounted total row ({total_row}).")

            # Assert that every possible total is there (including rows with only 0s)
            for l2_cat in tc_db_client.get_l2_categories(WBS):
                assert l2_cat in set(r.get(columns.WBS_L2) for r in totals)
                for l3_cat in tc_db_client.get_l3_categories_by_l2(WBS, l2_cat):
                    assert l3_cat in set(r.get(columns.WBS_L3) for r in totals)


class TestTableConfig:
    """Test table_config_db.py."""

    @staticmethod
    @patch(TC_DB_CLIENT + ".get_most_recent_doc")
    @patch(TC_DB_CLIENT + "._insert_replace")
    @patch("rest_server.databases.table_config_db.MAX_CACHE_AGE", 5)
    def test_caching(mock_ir: Any, mock_gmrd: Any) -> None:
        """Test functionality around `MAX_CACHE_AGE`."""
        assert table_config_db.MAX_CACHE_AGE == 5

        # Call #1
        mock_gmrd.side_effect = mongo_tools.DocumentNotFoundError()  # "db is empty"
        tc_db_client = table_config_db.TableConfigDatabaseClient(sentinel.mongo)
        mock_ir.return_value = None  # no-op the db insert

        # assert call to db (from __init__())
        mock_gmrd.assert_called()
        reset_mock(mock_ir, mock_gmrd)

        # Call #2 - before cache time limit
        time.sleep(table_config_db.MAX_CACHE_AGE / 2)
        mock_gmrd.side_effect = mongo_tools.DocumentNotFoundError()  # "db is empty"
        mock_ir.return_value = None  # no-op the db insert

        # assert NO call to db
        tc_db_client.refresh()
        mock_gmrd.assert_not_called()
        reset_mock(mock_ir, mock_gmrd)

        # Call #3 - after cache time limit
        time.sleep(table_config_db.MAX_CACHE_AGE)
        mock_gmrd.side_effect = mongo_tools.DocumentNotFoundError()  # "db is empty"
        mock_ir.return_value = None  # no-op the db insert

        # assert call to db
        tc_db_client.refresh()
        mock_gmrd.assert_called()
        reset_mock(mock_ir, mock_gmrd)

    @staticmethod
    @patch(TC_DB_CLIENT + ".get_most_recent_doc")
    @patch(TC_DB_CLIENT + "._insert_replace")
    def test_us_or_non_us(mock_ir: Any, mock_gmrd: Any) -> None:
        """Test _us_or_non_us().

        Function is very simple, so also test institution-dict's format.
        """
        # Setup & Mock
        mock_gmrd.side_effect = mongo_tools.DocumentNotFoundError()  # "db is empty"
        tc_db_client = table_config_db.TableConfigDatabaseClient(sentinel.mongo)
        mock_ir.return_value = None  # no-op the db insert

        for inst in tc_db_client.institution_dicts().values():
            assert "abbreviation" in inst
            assert "is_US" in inst
            assert inst["is_US"] is True or inst["is_US"] is False
            if inst["is_US"]:
                assert tc_db_client.us_or_non_us(inst["abbreviation"]) == "US"
            else:
                assert tc_db_client.us_or_non_us(inst["abbreviation"]) == "Non-US"
