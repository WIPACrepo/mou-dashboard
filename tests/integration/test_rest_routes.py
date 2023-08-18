"""Integration test rest_server module.

NOTE: THESE TESTS NEED TO RUN IN ORDER -- STATE DEPENDENT
"""


# pylint: disable=W0212,W0621


import base64

# import sys
import time

import pytest
import requests
from rest_tools.client import RestClient  # type: ignore

# sys.path.append(".")
# from rest_server import routes  # isort:skip  # noqa # pylint: disable=E0401,C0413
# from rest_server import config  # isort:skip  # noqa # pylint: disable=E0401,C0413
# from rest_server.utils import (  # isort:skip  # noqa # pylint: disable=E0401,C0413,C0411
#     types,
# )
# from rest_server.data_sources import (  # isort:skip  # noqa # pylint: disable=E0401,C0413
#     todays_institutions,
# )


WBS_L1 = "mo"


@pytest.fixture
def ds_rc() -> RestClient:
    """Get data source REST client via web_app."""
    return RestClient("http://localhost:8080", timeout=30, retries=0)


def test_ingest(ds_rc: RestClient) -> None:
    """Test POST /table/data.

    NOTE: Execute first, so other tests have data in the db.
    """
    filename = "./tests/integration/Dummy_WBS.xlsx"
    with open(filename, "rb") as f:
        base64_bin = base64.b64encode(f.read())
        base64_file = base64_bin.decode(encoding="utf-8")

    body = {"base64_file": base64_file, "filename": filename, "creator": "Hank"}
    resp = ds_rc.request_seq("POST", f"/table/data/{WBS_L1}", body)

    assert resp["n_records"]
    assert not resp["previous_snapshot"]
    assert (current_1 := resp["current_snapshot"])  # pylint: disable=C0325

    # Do it again...
    resp = ds_rc.request_seq("POST", f"/table/data/{WBS_L1}", body)

    assert resp["n_records"]
    assert (previous_2 := resp["previous_snapshot"])  # pylint: disable=C0325
    assert (current_2 := resp["current_snapshot"])  # pylint: disable=C0325
    assert (
        float(current_1["timestamp"])
        < float(previous_2["timestamp"])
        < float(current_2["timestamp"])
    )

    # Now fail...
    with pytest.raises(requests.exceptions.HTTPError):
        body = {"base64_file": "123456789", "filename": filename}
        resp = ds_rc.request_seq("POST", f"/table/data/{WBS_L1}", body)


class TestNoArgumentRoutes:
    """Test routes.py routes that don't require arguments."""

    @staticmethod
    def test_main_get(ds_rc: RestClient) -> None:
        """Test `GET` @ `/`."""
        # assert "get" in dir(routes.MainHandler)

        resp = ds_rc.request_seq("GET", "/")
        assert resp == {}

    @staticmethod
    def test_snapshots_timestamps_get(ds_rc: RestClient) -> None:
        """Test `GET` @ `/snapshots/list`."""
        # assert (
        #     routes.SnapshotsHandler.ROUTE
        #     == rf"/snapshots/list/(?P<wbs_l1>{routes._WBS_L1_REGEX_VALUES})$"
        # )
        # assert "get" in dir(routes.SnapshotsHandler)

        resp = ds_rc.request_seq("GET", f"/snapshots/list/{WBS_L1}")
        assert list(resp.keys()) == ["snapshots"]
        assert isinstance(resp["snapshots"], list)
        for snap in resp["snapshots"]:
            assert snap.keys() == ["timestamp", "name", "creator"]

    @staticmethod
    def test_snapshots_make_post() -> None:
        """Test `POST` @ `/snapshots/make`."""
        # assert (
        #     routes.MakeSnapshotHandler.ROUTE
        #     == rf"/snapshots/make/(?P<wbs_l1>{routes._WBS_L1_REGEX_VALUES})$"
        # )
        # assert "post" in dir(routes.MakeSnapshotHandler)

        # NOTE: reserve testing POST for test_snapshots()

    @staticmethod
    def test_snapshots(ds_rc: RestClient) -> None:
        """Test `POST` @ `/snapshots/make` and `GET` @ `/snapshots/list`."""
        # 3 snapshots were taken in test_ingest()
        assert (
            len(
                ds_rc.request_seq(
                    "GET", f"/snapshots/list/{WBS_L1}", {"is_admin": True}
                )["snapshots"]
            )
            == 3
        )

        assert not ds_rc.request_seq("GET", f"/snapshots/list/{WBS_L1}")["snapshots"]
        assert not ds_rc.request_seq(
            "GET", f"/snapshots/list/{WBS_L1}", {"is_admin": False}
        )["snapshots"]

        for i in range(1, 20):
            time.sleep(1)
            print(i)
            resp = ds_rc.request_seq(
                "POST",
                f"/snapshots/make/{WBS_L1}",
                {"name": f"#{i}", "creator": "Hank"},
            )
            assert list(resp.keys()) == ["name", "creator", "timestamp", "admin_only"]
            assert resp["name"] == f"#{i}"
            assert resp["creator"] == "Hank"
            now = time.time()
            assert now - float(resp["timestamp"]) < 2  # account for travel time

            # admin
            if i % 2 == 1:  # odd
                snapshots = ds_rc.request_seq(
                    "GET", f"/snapshots/list/{WBS_L1}", {"is_admin": True}
                )["snapshots"]
                assert len(snapshots) == i + 3
            # explicitly non-admin
            elif i % 4 == 0:  # every-4
                snapshots = ds_rc.request_seq(
                    "GET", f"/snapshots/list/{WBS_L1}", {"is_admin": False}
                )["snapshots"]
                assert len(snapshots) == i
            # implicitly non-admin
            else:  # every-4 off by 2
                assert i % 4 == 2
                snapshots = ds_rc.request_seq("GET", f"/snapshots/list/{WBS_L1}")[
                    "snapshots"
                ]
                assert len(snapshots) == i

            assert resp["timestamp"] in [s["timestamp"] for s in snapshots]

    @staticmethod
    def test_table_config_get(ds_rc: RestClient) -> None:
        """Test `GET` @ `/table/config`."""
        # assert routes.TableConfigHandler.ROUTE == r"/table/config$"
        # assert "get" in dir(routes.TableConfigHandler)

        resp = ds_rc.request_seq("GET", "/table/config")
        assert list(resp.keys()) == ["mo", "upgrade"]
        for tc_cfg in resp.values():
            assert list(tc_cfg.keys()) == [
                "columns",
                "simple_dropdown_menus",
                "labor_categories",
                "conditional_dropdown_menus",
                "dropdowns",
                "numerics",
                "non_editables",
                "hiddens",
                "tooltips",
                "widths",
                "border_left_columns",
                "page_size",
            ]

    # @staticmethod
    # def test_institution_static_get(ds_rc: RestClient) -> None:
    #     """Test `GET` @ `/institution/today`."""
    #     assert routes.InstitutionStaticHandler.ROUTE == r"/institution/today$"
    #     assert "get" in dir(routes.InstitutionStaticHandler)

    #     resp = ds_rc.request_seq("GET", "/institution/today")
    #     assert resp  # not empty
    #     assert isinstance(resp, dict)
    #     for inst, info in resp.items():
    #         assert " " not in inst
    #         # check all "-"-delimited substrings are initial-cased
    #         assert all(s[0].isupper() for s in inst.split("-"))
    #         todays_institutions.Institution(**info)  # try to cast it (atrrs & types)

    @staticmethod
    def test_institution_values(ds_rc: RestClient) -> None:
        """Test `/institution/values/`."""
        institutions = ["UDub", "UofA", "TechState"]

        for i, inst in enumerate(institutions):
            post_body = {
                "phds_authors": 55 * (i + 1),
                "faculty": 100 * (i + 1),
                "scientists_post_docs": 60 * (i + 1),
                "grad_students": 30 * (i + 1),
                "cpus": 5000 * (i + 1),
                "gpus": 500 * (i + 1),
                "text": f"hello world #{i}",
                "headcounts_confirmed": True,
                "computing_confirmed": True,
            }
            ds_rc.request_seq(
                "POST",
                f"/institution/values/{WBS_L1}",
                post_body | {"institution": inst},
            )

            resp = ds_rc.request_seq(
                "GET",
                f"/institution/values/{WBS_L1}",
                {"institution": inst},
            )
            assert resp == post_body

        snap_timestamp = ds_rc.request_seq(
            "POST",
            f"/snapshots/make/{WBS_L1}",
            {"name": "Homerun", "creator": "Ohtani"},
        )["timestamp"]

        # after snapshot all should be unconfirmed in LIVE_COLLECTION
        for i, inst in enumerate(institutions):
            resp = ds_rc.request_seq(
                "GET",
                f"/institution/values/{WBS_L1}",
                {"institution": inst},
            )
            assert not resp["headcounts_confirmed"]
            assert not resp["computing_confirmed"]
            # snapshot should be unchanged
            resp = ds_rc.request_seq(
                "GET",
                f"/institution/values/{WBS_L1}",
                {"institution": inst, "snapshot_timestamp": snap_timestamp},
            )
            assert resp["headcounts_confirmed"]
            assert resp["computing_confirmed"]


class TestTableHandler:
    """Test `/table/data`."""

    @staticmethod
    def test_sanity() -> None:
        """Check routes and methods are there."""
        # assert (
        #     routes.TableHandler.ROUTE
        #     == rf"/table/data/(?P<wbs_l1>{routes._WBS_L1_REGEX_VALUES})$"
        # )
        # assert "get" in dir(routes.TableHandler)

    @staticmethod
    def test_get_w_bad_args(ds_rc: RestClient) -> None:
        """Test `GET` @ `/table/data` with bad arguments."""
        # there are no required args
        _ = ds_rc.request_seq("GET", f"/table/data/{WBS_L1}", {"foo": "bar"})
        _ = ds_rc.request_seq("GET", f"/table/data/{WBS_L1}")

    @staticmethod
    def _assert_schema(record: dict, has_total_rows: bool = False) -> None:
        # pprint.pprint(record)
        assert record
        required_keys = [
            "Date & Time of Last Edit",
            "FTE",
            "Grand Total",
            "Institution",
            "Labor Cat.",
            "Name",
            "Name of Last Editor",
            "Source of Funds (U.S. Only)",
            "Task Description",
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
        for snapshot in ds_rc.request_seq("GET", f"/snapshots/list/{WBS_L1}")[
            "snapshots"
        ]:
            resp = ds_rc.request_seq(
                "GET", f"/table/data/{WBS_L1}", {"snapshot": snapshot["timestamp"]}
            )
            for record in resp["table"]:
                self._assert_schema(record)


class TestRecordHandler:
    """Test `/record`."""

    @staticmethod
    def test_sanity() -> None:
        """Check routes and methods are there."""
        # assert (
        #     routes.RecordHandler.ROUTE
        #     == rf"/record/(?P<wbs_l1>{routes._WBS_L1_REGEX_VALUES})$"
        # )
        # assert "post" in dir(routes.RecordHandler)
        # assert "delete" in dir(routes.RecordHandler)

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
