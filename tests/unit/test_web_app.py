"""Unit test web_app module."""

# pylint: disable=W0212


import sys
from copy import deepcopy
from typing import Final

sys.path.append(".")
from web_app.utils import (  # isort:skip  # noqa # pylint: disable=E0401,C0413
    dash_utils,
    data_source,
    types,
)


class TestDashUtils:
    """Test dash_utils.py."""

    RECORD: Final[types.Record] = {"a": "AA", "b": "BB", "c": "CC"}

    def _get_new_record(self) -> types.Record:
        return deepcopy(self.RECORD)

    def test_add_original_copies_to_record(self) -> None:
        """Test add_original_copies_to_record()."""
        record = self._get_new_record()
        record_orig = deepcopy(record)

        for _ in range(2):
            record_out = dash_utils.add_original_copies_to_record(record)
            assert record_out == record  # check in-place update
            assert len(record) == 2 * len(record_orig)
            # check copied values
            for key in record_orig.keys():
                assert record_orig[key] == record[key]
                assert record_orig[key] == record[key + dash_utils._OC_SUFFIX]

    def test_add_original_copies_to_record_novel(self) -> None:
        """Test add_original_copies_to_record(novel=True)."""
        record = self._get_new_record()
        record_orig = deepcopy(record)

        for _ in range(2):
            record_out = dash_utils.add_original_copies_to_record(record, novel=True)
            assert record_out == record  # check in-place update
            assert len(record) == 2 * len(record_orig)
            # check copied values
            for key in record_orig.keys():
                assert record_orig[key] == record[key]
                # check only keys were copied with _OC_SUFFIX, not values
                assert record_orig[key] != record[key + dash_utils._OC_SUFFIX]
                assert record[key + dash_utils._OC_SUFFIX] == ""

    def test_without_original_copies_from_record(self) -> None:
        """Test without_original_copies_from_record()."""
        record = self._get_new_record()
        record_orig = deepcopy(record)

        dash_utils.add_original_copies_to_record(record)
        record_out = dash_utils.without_original_copies_from_record(record)

        assert record_out != record
        assert record_out == record_orig


class TestDataSource:
    """Test data_source.py."""
