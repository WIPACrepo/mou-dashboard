"""Unit test rest_server module."""


# pylint: disable=W0212


import sys

sys.path.append(".")
from rest_server.utils import (  # isort:skip  # noqa # pylint: disable=E0401,C0413
    db_utils,
    utils,
)


class TestDBUtils:
    """Test db_utils.py."""

    @staticmethod
    def test_init() -> None:
        """Test MoUMotorClient.__init__()."""
        pass

    @staticmethod
    def test_mongofy_key_name() -> None:
        """Test _mongofy_key_name()."""
        pass

    @staticmethod
    def test_demongofy_key_name() -> None:
        """Test _demongofy_key_name()."""
        pass

    @staticmethod
    def test_mongofy_record() -> None:
        """Test _mongofy_record()."""
        pass

    @staticmethod
    def test_demongofy_record() -> None:
        """Test _demongofy_record()."""
        pass

    @staticmethod
    def test_create_live_collection() -> None:
        """Test _create_live_collection()."""
        pass

    @staticmethod
    def test_ingest_xlsx() -> None:
        """Test _ingest_xlsx()."""
        pass

    @staticmethod
    def test_list_database_names() -> None:
        """Test _list_database_names()."""
        pass

    @staticmethod
    def test_get_db() -> None:
        """Test _get_db()."""
        pass

    @staticmethod
    def test_list_collection_names() -> None:
        """Test _list_collection_names()."""
        pass

    @staticmethod
    def test_get_collection() -> None:
        """Test _get_collection()."""
        pass

    @staticmethod
    def test_create_collection() -> None:
        """Test _create_collection()."""
        pass

    @staticmethod
    def test_ensure_collection_indexes() -> None:
        """Test _ensure_collection_indexes()."""
        pass

    @staticmethod
    def test_ensure_all_databases_indexes() -> None:
        """Test _ensure_all_databases_indexes()."""
        pass

    @staticmethod
    def test_get_table() -> None:
        """Test get_table()."""
        pass

    @staticmethod
    def test_upsert_record() -> None:
        """Test upsert_record()."""
        pass

    @staticmethod
    def test_delete_record() -> None:
        """Test delete_record()."""
        pass

    @staticmethod
    def test_ingest_new_snapshot_collection() -> None:
        """Test _ingest_new_snapshot_collection()."""
        pass

    @staticmethod
    def test_snapshot_live_collection() -> None:
        """Test snapshot_live_collection()."""
        pass

    @staticmethod
    def test_list_snapshot_timestamps() -> None:
        """Test list_snapshot_timestamps()."""
        pass

    @staticmethod
    def test_restore_record() -> None:
        """Test restore_record()."""
        pass


class TestUtils:
    """Test utils.py."""

    @staticmethod
    def test_remove_on_the_fly_fields() -> None:
        """Test remove_on_the_fly_fields()."""
        pass

    @staticmethod
    def test_get_fte_subcolumn() -> None:
        """Test _get_fte_subcolumn()."""
        pass

    @staticmethod
    def test_us_or_non_us() -> None:
        """Test _us_or_non_us()."""
        pass

    @staticmethod
    def test_add_on_the_fly_fields() -> None:
        """Test add_on_the_fly_fields()."""
        pass

    @staticmethod
    def test_insert_total_rows() -> None:
        """Test insert_total_rows()."""
        pass
