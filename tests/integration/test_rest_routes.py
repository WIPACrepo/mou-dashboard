"""Integration test rest_server module."""


# pylint: disable=W0212,W0621


import base64
import pprint
import sys
import time

import pytest
import requests

# local imports
from rest_tools.client import RestClient  # type: ignore

sys.path.append(".")
from rest_server import routes  # isort:skip  # noqa # pylint: disable=E0401,C0413
from rest_server.utils import (  # isort:skip  # noqa # pylint: disable=E0401,C0413,C0411
    types,
)
import web_app.data_source.utils  # isort:skip  # noqa # pylint: disable=E0401,C0413
import web_app.config  # isort:skip  # noqa # pylint: disable=E0401,C0413


WBS_L1 = "upgrade"


@pytest.fixture  # type: ignore
def ds_rc() -> RestClient:
    """Get data source REST client via web_app."""
    web_app.config.update_config_global()
    return web_app.data_source.utils._rest_connection()


def test_ingest(ds_rc: RestClient) -> None:
    """Test POST /table/data.

    Execute first, so other tests have data in the db.
    """
    filename = "./tests/integration/WBS.xlsx"
    with open(filename, "rb") as f:
        base64_bin = base64.b64encode(f.read())
        base64_file = base64_bin.decode(encoding="utf-8")

    body = {"base64_file": base64_file, "filename": filename}
    resp = ds_rc.request_seq("POST", f"/table/data/{WBS_L1}", body)

    assert resp["n_records"]
    assert not resp["previous_snapshot"]
    assert (current_1 := resp["current_snapshot"])  # pylint: disable=C0325

    # Do it again...
    resp = ds_rc.request_seq("POST", f"/table/data/{WBS_L1}", body)

    assert resp["n_records"]
    assert (previous_2 := resp["previous_snapshot"])  # pylint: disable=C0325
    assert (current_2 := resp["current_snapshot"])  # pylint: disable=C0325
    assert float(current_1) < float(previous_2) < float(current_2)

    # Now fail...
    with pytest.raises(requests.exceptions.HTTPError):
        body = {"base64_file": "123456789", "filename": filename}
        resp = ds_rc.request_seq("POST", f"/table/data/{WBS_L1}", body)


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
        assert (
            routes.SnapshotsHandler.ROUTE
            == rf"/snapshots/timestamps/(?P<wbs_l1>{routes._WBS_L1_REGEX_VALUES})$"
        )
        assert "get" in dir(routes.SnapshotsHandler)

        resp = ds_rc.request_seq("GET", f"/snapshots/timestamps/{WBS_L1}")
        assert list(resp.keys()) == ["timestamps"]
        assert isinstance(resp["timestamps"], list)

    @staticmethod
    def test_snapshots_make_post() -> None:
        """Test `POST` @ `/snapshots/make`."""
        assert (
            routes.MakeSnapshotHandler.ROUTE
            == rf"/snapshots/make/(?P<wbs_l1>{routes._WBS_L1_REGEX_VALUES})$"
        )
        assert "post" in dir(routes.MakeSnapshotHandler)

        # NOTE: reserve testing POST for test_snapshots()

    @staticmethod
    def test_snapshots(ds_rc: RestClient) -> None:
        """Test `POST` @ `/snapshots/make` and `GET` @ `/snapshots/timestamps`."""
        # 3 snapshots were taken in test_ingest()
        assert (
            len(
                ds_rc.request_seq("GET", f"/snapshots/timestamps/{WBS_L1}")[
                    "timestamps"
                ]
            )
            == 3
        )

        for i in range(4, 100):
            time.sleep(1)
            print(i)
            resp = ds_rc.request_seq("POST", "/snapshots/make")
            assert list(resp.keys()) == ["timestamp"]
            now = time.time()
            assert now - float(resp["timestamp"]) < 2  # account for travel time

            timestamps = ds_rc.request_seq("GET", f"/snapshots/timestamps/{WBS_L1}")[
                "timestamps"
            ]
            assert len(timestamps) == i
            assert resp["timestamp"] in timestamps

    @staticmethod
    def test_table_config_get(ds_rc: RestClient) -> None:
        """Test `GET` @ `/table/config`."""
        assert routes.TableConfigHandler.ROUTE == r"/table/config$"
        assert "get" in dir(routes.TableConfigHandler)

        resp = ds_rc.request_seq("GET", f"/table/config")
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
        assert (
            routes.TableHandler.ROUTE
            == rf"/table/data/(?P<wbs_l1>{routes._WBS_L1_REGEX_VALUES})$"
        )
        assert "get" in dir(routes.TableHandler)

    @staticmethod
    def test_get_w_bad_args(ds_rc: RestClient) -> None:
        """Test `GET` @ `/table/data` with bad arguments."""
        # there are no required args
        _ = ds_rc.request_seq("GET", f"/table/data/{WBS_L1}", {"foo": "bar"})
        _ = ds_rc.request_seq("GET", f"/table/data/{WBS_L1}")

    @staticmethod
    def _assert_schema(record: types.Record, has_total_rows: bool = False) -> None:
        pprint.pprint(record)
        assert record
        required_keys = [
            "FTE",
            "Grand Total",
            "Institution",
            "Labor Cat.",
            "Names",
            "Source of Funds (U.S. Only)",
            "Tasks",
            "US / Non-US",
            "WBS L2",
            "WBS L3",
            "_id",
        ]
        optional_keys = [
            "Non-US In-Kind",
            "US In-Kind",
            "NSF Base Grants",
            "NSF M&O Core",
        ]

        # has all required keys
        assert not any(r for r in required_keys if r not in record)

        # normal rows, only have one extra key
        # total rows have all of them
        extras = set(record.keys()) - set(required_keys)
        if has_total_rows:
            assert len(extras) in [len(optional_keys), 1]
        else:
            assert len(extras) == 1

        # any extra keys are in optional_keys
        assert not any(e for e in extras if e not in optional_keys)

    def test_get_schema(self, ds_rc: RestClient) -> None:
        """Test `GET` @ `/table/data`."""
        # assert schema in Live Collection
        for record in ds_rc.request_seq("GET", f"/table/data/{WBS_L1}")["table"]:
            self._assert_schema(record)

        # assert schema in Snapshot Collections
        for snapshot in ds_rc.request_seq("GET", f"/snapshots/timestamps/{WBS_L1}")[
            "timestamps"
        ]:
            resp = ds_rc.request_seq(
                "GET", f"/table/data/{WBS_L1}", {"snapshot": snapshot}
            )
            for record in resp["table"]:
                self._assert_schema(record)


class TestRecordHandler:
    """Test `/record`."""

    @staticmethod
    def test_sanity() -> None:
        """Check routes and methods are there."""
        assert (
            routes.RecordHandler.ROUTE
            == rf"/record/(?P<wbs_l1>{routes._WBS_L1_REGEX_VALUES})$"
        )
        assert "post" in dir(routes.RecordHandler)
        assert "delete" in dir(routes.RecordHandler)

    @staticmethod
    def test_post_w_bad_args(ds_rc: RestClient) -> None:
        """Test `POST` @ `/record` with bad arguments."""
        # 'record' is the only required arg
        with pytest.raises(requests.exceptions.HTTPError):
            _ = ds_rc.request_seq("POST", f"/record/{WBS_L1}", {"foo": "bar"})

        with pytest.raises(requests.exceptions.HTTPError):
            _ = ds_rc.request_seq("POST", f"/record/{WBS_L1}")

        with pytest.raises(requests.exceptions.HTTPError):
            _ = ds_rc.request_seq("POST", f"/record/{WBS_L1}", {"institution": "foo"})

        with pytest.raises(requests.exceptions.HTTPError):
            _ = ds_rc.request_seq("POST", f"/record/{WBS_L1}", {"labor": "bar"})

        with pytest.raises(requests.exceptions.HTTPError):
            _ = ds_rc.request_seq(
                "POST", f"/record/{WBS_L1}", {"institution": "foo", "labor": "bar"}
            )

    @staticmethod
    def test_delete_w_bad_args(ds_rc: RestClient) -> None:
        """Test `DELETE` @ `/record` with bad arguments."""
        # 'record' is the only required arg
        with pytest.raises(requests.exceptions.HTTPError):
            _ = ds_rc.request_seq("DELETE", f"/record/{WBS_L1}", {"foo": "bar"})

        with pytest.raises(requests.exceptions.HTTPError):
            _ = ds_rc.request_seq("DELETE", f"/record/{WBS_L1}")
