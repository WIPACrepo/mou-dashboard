"""Unit test rest_server module."""


import sys

# pylint: disable=W0212
from typing import Any, List
from unittest.mock import ANY, AsyncMock, MagicMock, Mock, patch, sentinel

import pytest
from bson.objectid import ObjectId  # type: ignore[import]

sys.path.append(".")
from rest_server.utils import (  # isort:skip  # noqa # pylint: disable=E0401,C0413
    db_utils,
    utils,
    types,
)


MOU_MOTOR_CLIENT = "rest_server.utils.db_utils.MoUMotorClient"


def reset_mock(*args: Mock) -> None:
    """Reset all the Mock objects given."""
    for a in args:  # pylint: disable=C0103
        a.reset_mock()


class TestDBUtils:  # pylint: disable=R0904
    """Test db_utils.py."""

    @staticmethod
    @pytest.fixture  # type: ignore
    def mock_mongo(mocker: Any) -> Any:
        """Patch mock_mongo."""
        mock_mongo = mocker.patch("motor.motor_tornado.MotorClient")
        mock_mongo.list_database_names.side_effect = AsyncMock()
        # TODO: add other mocked async methods, as needed
        return mock_mongo

    @staticmethod
    @patch(MOU_MOTOR_CLIENT + "._ensure_all_databases_indexes")
    @patch(MOU_MOTOR_CLIENT + "._ingest_xlsx")
    def test_init(mock_ix: Any, mock_eadi: Any) -> None:
        """Test MoUMotorClient.__init__()."""
        moumc = db_utils.MoUMotorClient(sentinel._client)
        assert moumc._client == sentinel._client
        mock_eadi.assert_called()
        mock_ix.assert_not_called()

        # with pytest.raises(AssertionError):
        #     # NOTE: this won't work b/c we mocked the caller (mock_eadi)
        #     # so, test further-down calls in their own tests (test_ensure_all_databases_indexes)
        #     mock_mongo.list_database_names.assert_called()

        # test w/ xlsx
        reset_mock(mock_eadi, mock_ix)
        moumc = db_utils.MoUMotorClient(sentinel._client, xlsx="./foo.xlsx")
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
    def test_create_live_collection() -> None:
        """Test _create_live_collection()."""

    @staticmethod
    def test_ingest_xlsx() -> None:
        """Test _ingest_xlsx()."""

    @staticmethod
    def test_list_database_names() -> None:
        """Test _list_database_names()."""

    @staticmethod
    def test_get_db() -> None:
        """Test _get_db()."""

    @staticmethod
    def test_list_collection_names() -> None:
        """Test _list_collection_names()."""

    @staticmethod
    def test_get_collection() -> None:
        """Test _get_collection()."""

    @staticmethod
    def test_create_collection() -> None:
        """Test _create_collection()."""

    @staticmethod
    def test_ensure_collection_indexes() -> None:
        """Test _ensure_collection_indexes()."""

    @staticmethod
    def test_ensure_all_databases_indexes() -> None:
        """Test _ensure_all_databases_indexes()."""

    @staticmethod
    def test_get_table() -> None:
        """Test get_table()."""

    @staticmethod
    def test_upsert_record() -> None:
        """Test upsert_record()."""

    @staticmethod
    def test_delete_record() -> None:
        """Test delete_record()."""

    @staticmethod
    def test_ingest_new_snapshot_collection() -> None:
        """Test _ingest_new_snapshot_collection()."""

    @staticmethod
    def test_snapshot_live_collection() -> None:
        """Test snapshot_live_collection()."""

    @staticmethod
    def test_list_snapshot_timestamps() -> None:
        """Test list_snapshot_timestamps()."""

    @staticmethod
    def test_restore_record() -> None:
        """Test restore_record()."""


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
