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


class TestUtils:
    """Test utils.py."""
