"""Unit test rest_server module."""


import sys

# pylint: disable=W0212
from typing import Any, Final, List
from unittest.mock import ANY, AsyncMock, call, MagicMock, Mock, patch, sentinel

import nest_asyncio  # type: ignore[import]
import pytest
import tornado
from bson.objectid import ObjectId  # type: ignore[import]

from rest_server import (  # isort:skip  # noqa # pylint: disable=E0401,C0413
    config,
    table_config,
)

sys.path.append(".")
from rest_server.utils import (  # isort:skip  # noqa # pylint: disable=E0401,C0413
    db_utils,
    utils,
    types,
)

nest_asyncio.apply()


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
        # TODO: add other mocked async methods, as needed
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
        keys = ["", "...", " ", "N;M"]
        mongofied_keys = ["", ";;;", " ", "N;M"]

        for key, mkey in zip(keys, mongofied_keys):
            assert db_utils.MoUMotorClient._mongofy_key_name(key) == mkey

    @staticmethod
    def test_demongofy_key_name() -> None:
        """Test _demongofy_key_name()."""
        keys = ["", ";;;", " ", "A;C", "."]
        demongofied_keys = ["", "...", " ", "A.C", "."]

        for key, dkey in zip(keys, demongofied_keys):
            assert db_utils.MoUMotorClient._demongofy_key_name(key) == dkey

    @staticmethod
    def test_mongofy_record() -> None:
        """Test _mongofy_record()."""
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

        for record, mrecord in zip(records, mongofied_records):
            assert db_utils.MoUMotorClient._mongofy_record(record) == mrecord

    @staticmethod
    def test_demongofy_record() -> None:
        """Test _demongofy_record()."""
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

        for record, drecord in zip(records, demongofied_records):
            assert db_utils.MoUMotorClient._demongofy_record(record) == drecord

        with pytest.raises(KeyError):
            db_utils.MoUMotorClient._demongofy_record({"a;b": 5, "Foo;Bar": "Baz"})

    @staticmethod
    @pytest.mark.asyncio  # type: ignore[misc]
    @patch(MOU_MOTOR_CLIENT + "._create_collection")
    async def test_create_live_collection(mock_cc: Any, mock_mongo: Any) -> None:
        """Test _create_live_collection()."""
        # Mock
        db_utils._LIVE_COLLECTION = sentinel.live_collection
        mock_cc.return_value = AsyncMock()
        mock_cc.insert_many.side_effect = AsyncMock()

        # Call
        moumc = db_utils.MoUMotorClient(mock_mongo)
        await moumc._create_live_collection(MagicMock())

        # Assert
        mock_cc.assert_called_with(sentinel.live_collection)

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
        await moumc._ingest_xlsx(MagicMock())

        # Assert
        assert mock_mr.call_count == len(rows)
        mock_mr.assert_called_with(rows[-1])
        mock_insc.awaited_once()
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
        await moumc._ingest_xlsx(MagicMock())

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
    async def test_create_collection(
        mock_eci: Any, mock_gdb: Any, mock_mongo: Any
    ) -> None:
        """Test _create_collection()."""
        # Mock
        mock_gdb.return_value.__getitem__.return_value = sentinel.coll_obj
        moumc = db_utils.MoUMotorClient(mock_mongo)

        # Call
        ret = await moumc._create_collection(ANY)

        # Assert
        assert ret == sentinel.coll_obj

        # test w/ Error
        # Mock
        reset_mock(mock_gdb, mock_mongo)
        mock_gdb.return_value.__getitem__.side_effect = KeyError
        mock_gdb.return_value.create_collection.return_value = sentinel.coll_obj
        mock_eci.side_effect = AsyncMock()
        moumc = db_utils.MoUMotorClient(mock_mongo)

        # Call
        ret = await moumc._create_collection(sentinel.coll)

        # Assert
        mock_gdb.return_value.create_collection.assert_called_once_with(sentinel.coll)
        mock_eci.assert_awaited_once_with(sentinel.coll, ANY)
        assert ret == sentinel.coll_obj

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
        assert mock_mkn.call_args_list == [
            call(table_config.INSTITUTION),
            call(table_config.LABOR_CAT),
        ]
        assert len(mock_gc.return_value.create_index.side_effect.await_args) == 2

    # NOTE: public methods are tested in integration tests


class TestUtils:
    """Test utils.py."""

    @staticmethod
    def test_remove_on_the_fly_fields() -> None:
        """Test remove_on_the_fly_fields()."""

    @staticmethod
    def test_get_fte_subcolumn() -> None:
        """Test _get_fte_subcolumn()."""

    @staticmethod
    def test_us_or_non_us() -> None:
        """Test _us_or_non_us()."""

    @staticmethod
    def test_add_on_the_fly_fields() -> None:
        """Test add_on_the_fly_fields()."""

    @staticmethod
    def test_insert_total_rows() -> None:
        """Test insert_total_rows()."""
