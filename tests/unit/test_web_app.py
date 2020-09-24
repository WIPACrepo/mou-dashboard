"""Unit test web_app module."""


import sys

sys.path.append(".")
from web_app.utils import (  # isort:skip  # noqa # pylint: disable=E0401,C0413
    dash_utils,
    data_source,
)


class TestDashUtils:
    """Test dash_utils.py."""

    def test_add_original_copies_to_record(self) -> None:
        dash_utils.add_original_copies_to_record({})


class TestDataSource:
    """Test data_source.py."""
