"""Unit test rest_server module."""


import copy
import pprint
import sys

# pylint: disable=W0212
from typing import Any, Final, List
from unittest.mock import ANY, AsyncMock, call, MagicMock, Mock, patch, sentinel

import nest_asyncio  # type: ignore[import]
import pytest
import tornado
from bson.objectid import ObjectId  # type: ignore[import]

from . import data

sys.path.append(".")
from rest_server.utils import (  # isort:skip  # noqa # pylint: disable=E0401,C0413,C0411
    db_utils,
    utils,
    types,
)
from rest_server import (  # isort:skip  # noqa # pylint: disable=E0401,C0413,C0411
    config,
    table_config as tc,
)


nest_asyncio.apply()  # allows nested event loops


MOU_MOTOR_CLIENT: Final[str] = "rest_server.utils.db_utils.MoUMotorClient"
MOTOR_CLIENT: Final[str] = "motor.motor_tornado.MotorClient"


def reset_mock(*args: Mock) -> None:
    """Reset all the Mock objects given."""
    for a in args:  # pylint: disable=C0103
        a.reset_mock()


class TestDBUtils:  # pylint: disable=R0904
    """Test private methods in db_utils.py."""

    @staticmethod
    @pytest.fixture  # type: ignore
    def mock_mongo(mocker: Any) -> Any:
        """Patch mock_mongo."""
        mock_mongo = mocker.patch(MOTOR_CLIENT)
        mock_mongo.list_database_names.side_effect = AsyncMock()
        return mock_mongo

    @staticmethod
    @patch(MOU_MOTOR_CLIENT + "._ensure_all_databases_indexes")
    @patch(MOU_MOTOR_CLIENT + "._ingest_xlsx")
    def test_init(mock_ix: Any, mock_eadi: Any) -> None:
        """Test MoUMotorClient.__init__()."""
        # Call
        moumc = db_utils.MoUMotorClient(sentinel._client)

        # Assert
        assert moumc._client == sentinel._client
        mock_eadi.assert_called()
        mock_ix.assert_not_called()

        # --- test w/ xlsx
        # Mock
        reset_mock(mock_eadi, mock_ix)

        # Call
        moumc = db_utils.MoUMotorClient(sentinel._client, xlsx="./foo.xlsx")

        # Assert
        assert moumc._client == sentinel._client
        mock_eadi.assert_called()
        mock_ix.assert_called_with("./foo.xlsx")

    @staticmethod
    def test_mongofy_key_name() -> None:
        """Test _mongofy_key_name()."""
        # Set-Up
        keys = ["", "...", " ", "N;M"]
        mongofied_keys = ["", ";;;", " ", "N;M"]

        # Call & Assert
        for key, mkey in zip(keys, mongofied_keys):
            assert db_utils.MoUMotorClient._mongofy_key_name(key) == mkey

    @staticmethod
    def test_demongofy_key_name() -> None:
        """Test _demongofy_key_name()."""
        # Set-Up
        keys = ["", ";;;", " ", "A;C", "."]
        demongofied_keys = ["", "...", " ", "A.C", "."]

        # Call & Assert
        for key, dkey in zip(keys, demongofied_keys):
            assert db_utils.MoUMotorClient._demongofy_key_name(key) == dkey

    @staticmethod
    @patch(MOU_MOTOR_CLIENT + "._validate_record_data")
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
            assert db_utils.MoUMotorClient._mongofy_record(record) == mrecord

    @staticmethod
    def test_demongofy_record() -> None:
        """Test _demongofy_record()."""
        # Set-Up
        records: List[types.Record] = [
            {"_id": ANY},
            {"_id": ANY, db_utils.IS_DELETED: True},
            {"_id": ANY, db_utils.IS_DELETED: False},
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
            assert db_utils.MoUMotorClient._demongofy_record(record) == drecord

        # Error Case
        with pytest.raises(KeyError):
            db_utils.MoUMotorClient._demongofy_record({"a;b": 5, "Foo;Bar": "Baz"})

    @staticmethod
    @pytest.mark.asyncio  # type: ignore[misc]
    @patch(MOU_MOTOR_CLIENT + "._ingest_new_collection")
    async def test_create_live_collection(mock_inc: Any, mock_mongo: Any) -> None:
        """Test _create_live_collection()."""
        # Mock
        db_utils._LIVE_COLLECTION = sentinel.live_collection
        mock_inc.return_value = AsyncMock()
        mock_inc.insert_many.side_effect = AsyncMock()

        # Call
        moumc = db_utils.MoUMotorClient(mock_mongo)
        await moumc._create_live_collection(MagicMock())

        # Assert
        mock_inc.assert_called_with(sentinel.live_collection, ANY)

    @staticmethod
    @pytest.mark.asyncio  # type: ignore[misc]
    @patch(MOU_MOTOR_CLIENT + "._ingest_new_snapshot_collection")
    @patch(MOU_MOTOR_CLIENT + "._create_live_collection")
    @patch(MOU_MOTOR_CLIENT + "._mongofy_record")
    @patch(MOU_MOTOR_CLIENT + "._list_collection_names")
    @patch("pandas.read_excel")
    async def test_ingest_xlsx(  # pylint: disable=R0913
        mock_pre: Any,
        mock_lcn: Any,
        mock_mr: Any,
        mock_clc: Any,
        mock_insc: Any,
        mock_mongo: Any,
    ) -> None:
        """Test _ingest_xlsx()."""
        # Mock
        rows = [
            {sentinel.key1: sentinel.val1, sentinel.key2: sentinel.val2},
            {sentinel.key3: sentinel.val3},
        ]
        mock_pre.return_value.fillna.return_value.to_dict.return_value = rows

        # Call
        moumc = db_utils.MoUMotorClient(mock_mongo)
        await moumc.ingest_xlsx(MagicMock())

        # Assert
        assert mock_mr.call_count == len(rows)
        mock_mr.assert_called_with(rows[-1])
        mock_insc.assert_awaited_once()
        assert len(mock_insc.await_args) == len(rows)
        mock_lcn.assert_awaited_once()
        mock_clc.assert_awaited_once()
        assert len(mock_clc.await_args) == len(rows)

        # test w/ live collection
        # Mock
        reset_mock(mock_pre, mock_lcn, mock_mr, mock_clc, mock_insc, mock_mongo)
        mock_lcn.return_value = [db_utils._LIVE_COLLECTION]

        # Call
        moumc = db_utils.MoUMotorClient(mock_mongo)
        await moumc.ingest_xlsx(MagicMock())

        # Assert
        assert mock_mr.call_count == len(rows)
        mock_mr.assert_called_with(rows[-1])
        mock_insc.assert_awaited_once()
        assert len(mock_insc.await_args) == len(rows)
        mock_lcn.assert_awaited_once()
        mock_clc.assert_not_called()

    @staticmethod
    @pytest.mark.asyncio  # type: ignore[misc]
    async def test_list_database_names(mock_mongo: Any) -> None:
        """Test _list_database_names()."""
        # Mock
        dbs = ["foo", "bar", "baz"] + config.EXCLUDE_DBS[:3]
        moumc = db_utils.MoUMotorClient(mock_mongo)
        mock_mongo.list_database_names.side_effect = AsyncMock(return_value=dbs)

        # Call
        ret = await moumc._list_database_names()

        # Assert
        assert ret == dbs[:3]
        assert mock_mongo.list_database_names.side_effect.await_count == 1

    @staticmethod
    def test_get_db(mock_mongo: Any) -> None:
        """Test _get_db()."""
        # Mock
        mock_mongo.__getitem__.return_value = sentinel.db_obj
        moumc = db_utils.MoUMotorClient(mock_mongo)

        # Call
        ret = moumc._get_db(ANY)

        # Assert
        assert ret == sentinel.db_obj

        # test w/ Error
        # Mock
        reset_mock(mock_mongo)
        mock_mongo.__getitem__.side_effect = KeyError
        moumc = db_utils.MoUMotorClient(mock_mongo)

        # Call
        with pytest.raises(tornado.web.HTTPError):
            ret = moumc._get_db(ANY)

        # test w/ Error
        # Mock
        reset_mock(mock_mongo)
        mock_mongo.__getitem__.side_effect = TypeError
        moumc = db_utils.MoUMotorClient(mock_mongo)

        # Call
        with pytest.raises(tornado.web.HTTPError):
            ret = moumc._get_db(ANY)

    @staticmethod
    @pytest.mark.asyncio  # type: ignore[misc]
    @patch(MOU_MOTOR_CLIENT + "._get_db")
    async def test_list_collection_names(mock_gdb: Any, mock_mongo: Any) -> None:
        """Test _list_collection_names()."""
        # Mock
        colls = ["foo", "bar", "baz"] + config.EXCLUDE_COLLECTIONS[:3]
        moumc = db_utils.MoUMotorClient(mock_mongo)
        mock_gdb.return_value.list_collection_names.side_effect = AsyncMock(
            return_value=colls
        )

        # Call
        ret = await moumc._list_collection_names()

        # Assert
        assert ret == colls[:3]
        mock_gdb.return_value.list_collection_names.side_effect.assert_awaited_once()

    @staticmethod
    @patch(MOU_MOTOR_CLIENT + "._get_db")
    def test_get_collection(mock_gdb: Any, mock_mongo: Any) -> None:
        """Test _get_collection()."""
        # Mock
        mock_gdb.return_value.__getitem__.return_value = sentinel.coll_obj
        moumc = db_utils.MoUMotorClient(mock_mongo)

        # Call
        ret = moumc._get_collection(ANY)

        # Assert
        assert ret == sentinel.coll_obj

        # test w/ Error
        # Mock
        reset_mock(mock_gdb, mock_mongo)
        mock_gdb.return_value.__getitem__.side_effect = KeyError
        moumc = db_utils.MoUMotorClient(mock_mongo)

        # Call
        with pytest.raises(tornado.web.HTTPError):
            ret = moumc._get_collection(ANY)

    @staticmethod
    @pytest.mark.asyncio  # type: ignore[misc]
    @patch(MOU_MOTOR_CLIENT + "._get_db")
    @patch(MOU_MOTOR_CLIENT + "._ensure_collection_indexes")
    @patch(MOU_MOTOR_CLIENT + "._mongofy_record")
    async def test_ingest_new_collection(
        mock_mr: Any, mock_eci: Any, mock_gdb: Any, mock_mongo: Any
    ) -> None:
        """Test _ingest_new_collection()."""
        # Mock
        mock_gdb.return_value.__getitem__.return_value.insert_many.side_effect = (
            AsyncMock()
        )
        moumc = db_utils.MoUMotorClient(mock_mongo)
        mock_mr.return_value = [ANY, ANY]

        # Call
        await moumc._ingest_new_collection(MagicMock(), [ANY, ANY])

        # Assert
        pass  # pylint: disable=W0107

        # test w/ Error
        # Mock
        reset_mock(mock_gdb, mock_mongo)
        mock_gdb.return_value.__getitem__.side_effect = KeyError
        mock_gdb.return_value.create_collection.return_value.insert_many.side_effect = (
            AsyncMock()
        )
        mock_eci.side_effect = AsyncMock()
        moumc = db_utils.MoUMotorClient(mock_mongo)

        # Call
        await moumc._ingest_new_collection(sentinel.coll, [ANY, ANY])

        # Assert
        mock_gdb.return_value.create_collection.assert_called_once_with(sentinel.coll)
        mock_eci.assert_awaited_once_with(sentinel.coll, ANY)

    @staticmethod
    @pytest.mark.asyncio  # type: ignore[misc]
    @patch(MOU_MOTOR_CLIENT + "._get_collection")
    @patch(MOU_MOTOR_CLIENT + "._mongofy_key_name")
    async def test_ensure_collection_indexes(
        mock_mkn: Any, mock_gc: Any, mock_mongo: Any
    ) -> None:
        """Test _ensure_collection_indexes()."""
        # Mock
        mock_gc.return_value.create_index.side_effect = AsyncMock()
        moumc = db_utils.MoUMotorClient(mock_mongo)

        # Call
        await moumc._ensure_collection_indexes(sentinel.coll)

        # Assert
        assert mock_mkn.call_count == 2
        assert mock_mkn.call_args_list == [call("Institution"), call("Labor Cat.")]
        assert len(mock_gc.return_value.create_index.side_effect.await_args) == 2

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
    def test_us_or_non_us() -> None:
        """Test _us_or_non_us().

        Function is very simple, so also test ICECUBE_INSTS's format.
        """
        for inst in utils.ICECUBE_INSTS.values():
            assert "abbreviation" in inst
            assert "is_US" in inst
            assert inst["is_US"] is True or inst["is_US"] is False
            if inst["is_US"]:
                assert utils._us_or_non_us(inst["abbreviation"]) == "US"
            else:
                assert utils._us_or_non_us(inst["abbreviation"]) == "Non-US"

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
            _ = utils.add_on_the_fly_fields({"foo": "bar", "FTE": 0})
        with pytest.raises(KeyError):
            _ = utils.add_on_the_fly_fields(
                {"foo": "bar", "FTE": 0, "Institution": "UW"}
            )
        _ = utils.add_on_the_fly_fields({"foo": "bar", "Institution": "SUNY"})
        with pytest.raises(KeyError):
            _ = utils.add_on_the_fly_fields(
                {
                    "foo": "bar",
                    "FTE": 0,
                    "Source of Funds (U.S. Only)": "NSF Base Grants",
                }
            )

    @staticmethod
    def test_insert_total_rows() -> None:
        """Test insert_total_rows().

        No need to integration test this.
        """
        #
        def _assert_funds_totals(_rows: types.Table, _total_row: types.Record) -> None:
            print("\n-----------------------------------------------------\n")
            pprint.pprint(_rows)
            pprint.pprint(_total_row)
            assert _total_row[tc.GRAND_TOTAL] == sum(r[tc.FTE] for r in _rows)
            for fund in [
                tc.NSF_MO_CORE,
                tc.NSF_BASE_GRANTS,
                tc.US_IN_KIND,
                tc.NON_US_IN_KIND,
            ]:
                assert _total_row[fund] == sum(
                    r[tc.FTE] for r in _rows if r[tc.SOURCE_OF_FUNDS_US_ONLY] == fund
                )

        # Test example table and empty table
        test_tables: Final[List[types.Table]] = [copy.deepcopy(data.FTE_ROWS), []]
        for table in test_tables:
            # Call
            totals = utils.get_total_rows(table)
            # pprint.pprint(totals)

            # Assert total sums
            for total_row in totals:

                # L3 US/Non-US Level
                if (
                    "L3 NON-US TOTAL" in total_row[tc.TOTAL_COL]  # type: ignore[operator]
                    or "L3 US TOTAL" in total_row[tc.TOTAL_COL]  # type: ignore[operator]
                ):
                    _assert_funds_totals(
                        [
                            r
                            for r in table
                            if total_row[tc.WBS_L2] == r[tc.WBS_L2]
                            and total_row[tc.WBS_L3] == r[tc.WBS_L3]
                            and total_row[tc.US_NON_US] == r[tc.US_NON_US]
                        ],
                        total_row,
                    )

                # L3 Level
                elif "L3 TOTAL" in total_row[tc.TOTAL_COL]:  # type: ignore[operator]
                    _assert_funds_totals(
                        [
                            r
                            for r in table
                            if total_row[tc.WBS_L2] == r[tc.WBS_L2]
                            and total_row[tc.WBS_L3] == r[tc.WBS_L3]
                        ],
                        total_row,
                    )

                # L2 Level
                elif "L2 TOTAL" in total_row[tc.TOTAL_COL]:  # type: ignore[operator]
                    _assert_funds_totals(
                        [r for r in table if total_row[tc.WBS_L2] == r[tc.WBS_L2]],
                        total_row,
                    )

                # Grand Total
                elif "GRAND TOTAL" in total_row[tc.TOTAL_COL]:  # type: ignore[operator]
                    _assert_funds_totals(table, total_row)

                # Other Kind?
                else:
                    raise Exception(f"Unaccounted total row ({total_row}).")

            # Assert that every possible total is there (including rows with only 0s)
            for l2_cat in tc.get_l2_categories():
                assert l2_cat in set(r.get(tc.WBS_L2) for r in totals)
                for l3_cat in tc.get_l3_categories_by_l2(l2_cat):
                    assert l3_cat in set(r.get(tc.WBS_L3) for r in totals)
