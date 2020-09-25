"""Unit test rest_server module."""


import sys

# pylint: disable=W0212
from typing import Any
from unittest.mock import ANY, AsyncMock, MagicMock, Mock, patch

import pytest

sys.path.append(".")
from rest_server.utils import (  # isort:skip  # noqa # pylint: disable=E0401,C0413
    db_utils,
    utils,
)


MOU_MOTOR_CLIENT = "rest_server.utils.db_utils.MoUMotorClient"


class TestDBUtils:  # pylint: disable=R0904
    """Test db_utils.py."""

    @staticmethod
    @pytest.fixture  # type: ignore
    def mock_mongo(mocker: Any) -> Any:
        """Patch mock_mongo."""
        mock_mongo = mocker.patch("motor.motor_tornado.MotorClient")
        mock_mongo.list_database_names.side_effect = AsyncMock()
        return mock_mongo

    @staticmethod
    @patch(MOU_MOTOR_CLIENT + "._ensure_all_databases_indexes")
    @patch(MOU_MOTOR_CLIENT + "._ingest_xlsx")
    def test_init(mock_ix: Any, mock_eadi: Any, mock_mongo: Any) -> None:
        """Test MoUMotorClient.__init__()."""
        _ = db_utils.MoUMotorClient(mock_mongo)
        mock_eadi.assert_called()
        mock_ix.assert_not_called()

        with pytest.raises(AssertionError):
            # NOTE: this won't work b/c we mocked the caller (mock_eadi)
            # so, test further-down calls in their own tests (test_ensure_all_databases_indexes)
            mock_mongo.list_database_names.assert_called()

        _ = db_utils.MoUMotorClient(mock_mongo, xlsx="./foo.xlsx")
        mock_eadi.assert_called()
        mock_ix.assert_called()

    @staticmethod
    def test_mongofy_key_name() -> None:
        """Test _mongofy_key_name()."""

    @staticmethod
    def test_demongofy_key_name() -> None:
        """Test _demongofy_key_name()."""

    @staticmethod
    def test_mongofy_record() -> None:
        """Test _mongofy_record()."""

    @staticmethod
    def test_demongofy_record() -> None:
        """Test _demongofy_record()."""

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
