"""Integration test rest_server module."""


# pylint: disable=W0212,W0621


import sys
import time

import pytest
import requests

# local imports
from rest_tools.client import RestClient  # type: ignore

sys.path.append(".")
from rest_server import routes  # isort:skip  # noqa # pylint: disable=E0401,C0413
import web_app.utils.data_source  # isort:skip  # noqa # pylint: disable=E0401,C0413


@pytest.fixture  # type: ignore
def ds_rc() -> RestClient:
    """Get data source REST client via web_app."""
    return web_app.utils.data_source._ds_rest_connection()


class TestNoArgumentRoutes:
    """Test routes.py routes that don't require arguments."""

    @staticmethod
    def test_main_get(ds_rc: RestClient) -> None:
        """Test `GET` @ `/`."""
        assert routes.MainHandler.ROUTE == r"/$"
        assert "get" in dir(routes.MainHandler)

        resp = ds_rc.request_seq("GET", "/")
        assert resp == {}

    @staticmethod
    def test_snapshots_timestamps_get(ds_rc: RestClient) -> None:
        """Test `GET` @ `/snapshots/timestamps`."""
        assert routes.SnapshotsHandler.ROUTE == r"/snapshots/timestamps$"
        assert "get" in dir(routes.SnapshotsHandler)

        resp = ds_rc.request_seq("GET", "/snapshots/timestamps")
        assert list(resp.keys()) == ["timestamps"]
        assert isinstance(resp["timestamps"], list)

    @staticmethod
    def test_snapshots_make_post(ds_rc: RestClient) -> None:
        """Test `POST` @ `/snapshots/make`."""
        assert routes.MakeSnapshotHandler.ROUTE == r"/snapshots/make$"
        assert "post" in dir(routes.MakeSnapshotHandler)

        resp = ds_rc.request_seq("POST", "/snapshots/make")
        assert list(resp.keys()) == ["timestamp"]
        assert int(time.time()) - int(resp["timestamp"]) < 2  # account for travel time

    @staticmethod
    def test_table_config_get(ds_rc: RestClient) -> None:
        """Test `GET` @ `/table/config`."""
        assert routes.TableConfigHandler.ROUTE == r"/table/config$"
        assert "get" in dir(routes.TableConfigHandler)

        resp = ds_rc.request_seq("GET", "/table/config")
        assert list(resp.keys()) == [
            "columns",
            "simple_dropdown_menus",
            "institutions",
            "labor_categories",
            "conditional_dropdown_menus",
            "dropdowns",
            "numerics",
            "non_editables",
            "hiddens",
            "widths",
            "border_left_columns",
            "page_size",
        ]


class TestTableHandler:
    """Test `/table/data`."""

    @staticmethod
    def test_sanity() -> None:
        """Check routes and methods are there."""
        assert routes.TableHandler.ROUTE == r"/table/data$"
        assert "get" in dir(routes.TableHandler)

    @staticmethod
    def test_get_bad_args(ds_rc: RestClient) -> None:
        """Test `GET` @ `/table/data`."""
        # there are no required args
        _ = ds_rc.request_seq("GET", "/table/data", {"foo": "bar"})
        _ = ds_rc.request_seq("GET", "/table/data")
        _ = ds_rc.request_seq("GET", "/table/data", None)


class TestRecordHandler:
    """Test `/record`."""

    @staticmethod
    def test_sanity() -> None:
        """Check routes and methods are there."""
        assert routes.RecordHandler.ROUTE == r"/record$"
        assert "post" in dir(routes.RecordHandler)
        assert "delete" in dir(routes.RecordHandler)

    @staticmethod
    def test_post_bad_args(ds_rc: RestClient) -> None:
        """Test `POST` @ `/record`."""
        # 'record' is the only required arg
        with pytest.raises(requests.exceptions.HTTPError):
            _ = ds_rc.request_seq("POST", "/record", {"foo": "bar"})

    @staticmethod
    def test_delete_bad_args(ds_rc: RestClient) -> None:
        """Test `DELETE` @ `/record`."""
        # 'record' is the only required arg
        with pytest.raises(requests.exceptions.HTTPError):
            _ = ds_rc.request_seq("DELETE", "/record", {"foo": "bar"})
