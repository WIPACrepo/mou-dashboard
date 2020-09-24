"""Integration test rest_server module."""


# pylint: disable=W0212


import sys

sys.path.append(".")
from rest_server import routes  # isort:skip  # noqa # pylint: disable=E0401,C0413


class TestRoutes:
    """Test routes.py."""
