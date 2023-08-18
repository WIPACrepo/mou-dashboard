"""Integration test rest_server module.

NOTE: THESE TESTS NEED TO RUN IN ORDER -- STATE DEPENDENT
"""


# pylint: disable=W0212,W0621


import base64
import dataclasses as dc
import os
import time
from typing import Any

import dacite
import pytest
import requests
from rest_tools.client import RestClient

# NOTE: universal_utils has no requirements -- only used to assert types
import universal_utils.types as uut  # isort:skip  # noqa: E402  # pylint: disable=wrong-import-position

WBS_L1 = "mo"


@pytest.fixture
def ds_rc() -> RestClient:
    """Get data source REST client."""
    return RestClient("http://localhost:8080", timeout=30, retries=0)


########################################################################################

SNAPSHOTS_DURING_INGESTION = 3

with open("./tests/integration/Dummy_WBS.xlsx", "rb") as f:
    INITIAL_INGEST_BODY = {
        "base64_file": base64.b64encode(f.read()).decode(encoding="utf-8"),
        "filename": f.name,
        "creator": "Hank",
        "is_admin": True,
    }


# NOTE: EXECUTED FIRST SO OTHER TESTS HAVE DATA IN THE DB
def test_ingest(ds_rc: RestClient) -> None:
    """Test POST /table/data."""
    match os.getenv("INTEGRATION_TEST_INGEST_TYPE"):
        case "xlsx":
            resp = ds_rc.request_seq(
                "POST", f"/table/data/{WBS_L1}", INITIAL_INGEST_BODY
            )
        case "mongodump_v2":
            # CI runner should have pre-ingested data
            resp = ds_rc.request_seq("GET", f"/table/data/{WBS_L1}", {"is_admin": True})
        case "mongodump_v3":
            # CI runner should have pre-ingested data
            resp = ds_rc.request_seq("GET", f"/table/data/{WBS_L1}", {"is_admin": True})
        case other:
            raise RuntimeError(
                f"did not receive valid 'INTEGRATION_TEST_INGEST_TYPE': {other}"
            )

    assert resp["n_records"]
    assert not resp["previous_snapshot"]
    assert (current_1 := resp["current_snapshot"])  # pylint: disable=C0325

    # Do it again...
    resp = ds_rc.request_seq("POST", f"/table/data/{WBS_L1}", INITIAL_INGEST_BODY)

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
        resp = ds_rc.request_seq(
            "POST",
            f"/table/data/{WBS_L1}",
            {"base64_file": "123456789", "filename": "foo-file", "is_admin": True},
        )


########################################################################################


class TestNoArgumentRoutes:
    """Test routes.py routes that don't require arguments."""

    @staticmethod
    def test_main_get(ds_rc: RestClient) -> None:
        """Test `GET` @ `/`."""
        resp = ds_rc.request_seq("GET", "/")
        assert resp == {}

    @staticmethod
    def test_snapshots_timestamps_get(ds_rc: RestClient) -> None:
        """Test `GET` @ `/snapshots/list`."""
        resp = ds_rc.request_seq("GET", f"/snapshots/list/{WBS_L1}", {"is_admin": True})
        assert list(resp.keys()) == ["snapshots"]
        assert isinstance(resp["snapshots"], list)
        for snap in resp["snapshots"]:
            assert list(snap.keys()) == ["timestamp", "name", "creator", "admin_only"]

    @staticmethod
    def test_snapshots_make_post() -> None:
        """Test `POST` @ `/snapshots/make`."""
        # NOTE: reserve testing POST for test_snapshots()

    @staticmethod
    def test_snapshots(ds_rc: RestClient) -> None:
        """Test `POST` @ `/snapshots/make` and `GET` @ `/snapshots/list`."""
        # snapshots taken in test_ingest()
        assert (
            len(
                ds_rc.request_seq(
                    "GET", f"/snapshots/list/{WBS_L1}", {"is_admin": True}
                )["snapshots"]
            )
            == SNAPSHOTS_DURING_INGESTION
        )
        # BUT those snaps were admin-only
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
            assert set(resp.keys()) == {"name", "creator", "timestamp", "admin_only"}
            assert resp["name"] == f"#{i}"
            assert resp["creator"] == "Hank"
            now = time.time()
            assert now - float(resp["timestamp"]) < 2  # account for travel time

            # admin
            if i % 2 == 1:  # odd
                snapshots = ds_rc.request_seq(
                    "GET", f"/snapshots/list/{WBS_L1}", {"is_admin": True}
                )["snapshots"]
                # first SNAPSHOTS_DURING_INGESTION were admin-only
                assert len(snapshots) == i + SNAPSHOTS_DURING_INGESTION
            # non-admin
            else:
                snapshots = ds_rc.request_seq(
                    "GET", f"/snapshots/list/{WBS_L1}", {"is_admin": False}
                )["snapshots"]
                assert len(snapshots) == i

            assert resp["timestamp"] in [s["timestamp"] for s in snapshots]

    @staticmethod
    def test_table_config_get(ds_rc: RestClient) -> None:
        """Test `GET` @ `/table/config`."""
        resp = ds_rc.request_seq("GET", "/table/config")
        assert list(resp.keys()) == ["mo", "upgrade"]
        for config in resp.values():
            assert list(config.keys()) == [
                "columns",
                "simple_dropdown_menus",
                "labor_categories",
                "conditional_dropdown_menus",
                "dropdowns",
                "numerics",
                "non_editables",
                "hiddens",
                "mandatories",
                "tooltips",
                "widths",
                "border_left_columns",
                "page_size",
            ]

    @staticmethod
    def test_institution_static_get(ds_rc: RestClient) -> None:
        """Test `GET` @ `/institution/today`."""
        resp = ds_rc.request_seq("GET", "/institution/today")
        assert resp  # not empty
        assert isinstance(resp, dict)
        for inst, info in resp.items():
            assert " " not in inst
            # check all "-"-delimited substrings are initial-cased
            assert all(s[0].isupper() for s in inst.split("-"))


class TestTableHandler:
    """Test `/table/data`."""

    @staticmethod
    def test_get_w_bad_args(ds_rc: RestClient) -> None:
        """Test `GET` @ `/table/data` with bad arguments."""
        tests: dict[str, dict[str, Any]] = {
            "is_admin": {"foo": "bar"},
        }
        for arg, body_min in tests.items():
            with pytest.raises(
                requests.exceptions.HTTPError,
                match=rf"400 Client Error: `{arg}`: \(MissingArgumentError\) .+ for url: {ds_rc.address}/table/data/{WBS_L1}",
            ):
                ds_rc.request_seq(
                    "GET",
                    f"/table/data/{WBS_L1}",
                    body_min,
                )

            # empty
            with pytest.raises(
                requests.exceptions.HTTPError,
                match=rf"400 Client Error: `is_admin`: \(MissingArgumentError\) .+ for url: {ds_rc.address}/table/data/{WBS_L1}",
            ):
                ds_rc.request_seq(
                    "GET",
                    f"/table/data/{WBS_L1}",
                )

    @staticmethod
    def _assert_schema(record: uut.DBRecord, has_total_rows: bool = False) -> None:
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
        for record in ds_rc.request_seq(
            "GET", f"/table/data/{WBS_L1}", {"is_admin": True}
        )["table"]:
            self._assert_schema(record)

        # assert schema in Snapshot Collections
        for snapshot in ds_rc.request_seq(
            "GET", f"/snapshots/list/{WBS_L1}", {"is_admin": True}
        )["snapshots"]:
            resp = ds_rc.request_seq(
                "GET",
                f"/table/data/{WBS_L1}",
                {"snapshot": snapshot["timestamp"], "is_admin": True},
            )
            for record in resp["table"]:
                self._assert_schema(record)


class TestRecordHandler:
    """Test `/record`."""

    @staticmethod
    def test_post_w_bad_args(ds_rc: RestClient) -> None:
        """Test `POST` @ `/record` with bad arguments."""
        tests: dict[str, dict[str, Any]] = {
            "record": {"editor": "me"},
            "editor": {"record": {"a": 1}},
        }
        for arg, body_min in tests.items():
            with pytest.raises(
                requests.exceptions.HTTPError,
                match=rf"400 Client Error: `{arg}`: \(MissingArgumentError\) .+ for url: {ds_rc.address}/record/{WBS_L1}",
            ):
                ds_rc.request_seq(
                    "POST",
                    f"/record/{WBS_L1}",
                    body_min,
                )

            # empty
            with pytest.raises(
                requests.exceptions.HTTPError,
                match=rf"400 Client Error: `record`: \(MissingArgumentError\) .+ for url: {ds_rc.address}/record/{WBS_L1}",
            ):
                ds_rc.request_seq(
                    "POST",
                    f"/record/{WBS_L1}",
                )

    @staticmethod
    def test_delete_w_bad_args(ds_rc: RestClient) -> None:
        """Test `DELETE` @ `/record` with bad arguments."""
        tests: dict[str, dict[str, Any]] = {
            "record_id": {"editor": "me"},
            "editor": {"record_id": {"a": 1}},
        }
        for arg, body_min in tests.items():
            with pytest.raises(
                requests.exceptions.HTTPError,
                match=rf"400 Client Error: `{arg}`: \(MissingArgumentError\) .+ for url: {ds_rc.address}/record/{WBS_L1}",
            ):
                ds_rc.request_seq(
                    "DELETE",
                    f"/record/{WBS_L1}",
                    body_min,
                )

            # empty
            with pytest.raises(
                requests.exceptions.HTTPError,
                match=rf"400 Client Error: `record_id`: \(MissingArgumentError\) .+ for url: {ds_rc.address}/record/{WBS_L1}",
            ):
                ds_rc.request_seq(
                    "DELETE",
                    f"/record/{WBS_L1}",
                )


class TestInstitutionValuesHandler:
    """Test `/institution/values/*`."""

    @staticmethod
    def test_institution_values_full_cycle(ds_rc: RestClient) -> None:
        """Test confirming admin-level re-touch-stoning."""
        local_insts: dict[str, uut.InstitutionValues] = {}
        first_post_insts = {
            "LBNL": uut.InstitutionValues(
                phds_authors=1,
                faculty=2,
                scientists_post_docs=3,
                grad_students=4,
                cpus=5,
                gpus=6,
                text="foo's test text",
            ),
            "DESY": uut.InstitutionValues(
                phds_authors=100,
                faculty=200,
                scientists_post_docs=300,
                grad_students=400,
                cpus=500,
                gpus=600,
                text="bar's test text",
            ),
            "Alberta": uut.InstitutionValues(
                phds_authors=51,
                faculty=52,
                scientists_post_docs=53,
                grad_students=54,
                cpus=55,
                gpus=56,
                text="baz's test text",
            ),
        }

        # Get values (should all be default values)
        for inst in first_post_insts:
            resp = ds_rc.request_seq(
                "GET", f"/institution/values/{WBS_L1}", {"institution": inst}
            )
            resp_instval = dacite.from_dict(uut.InstitutionValues, resp)
            assert resp_instval == uut.InstitutionValues()
            assert resp_instval.headcounts_metadata.has_valid_confirmation()
            assert resp_instval.table_metadata.has_valid_confirmation()
            assert resp_instval.computing_metadata.has_valid_confirmation()
            # update local storage
            local_insts[inst] = resp_instval

        # Add institution values
        time.sleep(1)
        assert local_insts
        for inst in local_insts:
            post_instval = first_post_insts.pop(inst)  # be done w/ this structure ASAP
            now = int(time.time())
            resp = ds_rc.request_seq(
                "POST", f"/institution/values/{WBS_L1}", post_instval.restful_dict(inst)
            )
            resp_instval = dacite.from_dict(uut.InstitutionValues, resp)
            assert abs(now - int(time.time())) <= 1
            assert any(
                resp_instval
                == dc.replace(
                    post_instval,
                    headcounts_metadata=uut.InstitutionAttrMetadata(
                        last_edit_ts=expected_ts,
                        confirmation_ts=0,
                        confirmation_touchstone_ts=0,
                    ),
                    table_metadata=uut.InstitutionAttrMetadata(
                        last_edit_ts=0, confirmation_ts=0, confirmation_touchstone_ts=0
                    ),
                    computing_metadata=uut.InstitutionAttrMetadata(
                        last_edit_ts=expected_ts,
                        confirmation_ts=0,
                        confirmation_touchstone_ts=0,
                    ),
                )
                for expected_ts in [now, now + 1]  # could be a bit slow
            )
            assert not resp_instval.headcounts_metadata.has_valid_confirmation()
            assert resp_instval.table_metadata.has_valid_confirmation()
            assert not resp_instval.computing_metadata.has_valid_confirmation()
            # update local storage
            local_insts[inst] = resp_instval

        # TEST EDITING TABLE
        time.sleep(1)
        assert local_insts
        for inst in local_insts:
            records = ds_rc.request_seq(
                "GET", f"/table/data/{WBS_L1}", {"institution": inst, "is_admin": True}
            )["table"]
            now = int(time.time())
            match inst:
                # add
                case "LBNL":
                    to_add = records[0]
                    to_add["_id"] = ""  # copy data, but don't replace records[0]
                    to_add["Name"] = "Leslie Knope"
                    resp = ds_rc.request_seq(
                        "POST",
                        f"/record/{WBS_L1}",
                        {
                            "record": to_add,
                            "editor": "Tom Haverford",
                        },
                    )
                # edit
                case "DESY":
                    to_add = records[0]
                    to_add["Name"] = "Jean-Ralphio"  # classic Jean-Ralphio...
                    resp = ds_rc.request_seq(
                        "POST",
                        f"/record/{WBS_L1}",
                        {
                            "record": to_add,
                            "editor": "Tom Haverford",
                        },
                    )
                # delete
                case "Alberta":
                    resp = ds_rc.request_seq(
                        "DELETE",
                        f"/record/{WBS_L1}",
                        {
                            "record_id": records[0]["_id"],
                            "editor": "Tom Haverford",
                        },
                    )
                case other:
                    raise ValueError(other)
            resp_instval = dacite.from_dict(
                uut.InstitutionValues, resp["institution_values"]
            )
            assert any(
                resp_instval
                == dc.replace(
                    local_insts[inst],
                    table_metadata=dc.replace(
                        resp_instval.table_metadata, last_edit_ts=expected_ts
                    ),
                )
                for expected_ts in [now, now + 1]  # could be a bit slow
            )
            assert not resp_instval.headcounts_metadata.has_valid_confirmation()
            assert not resp_instval.table_metadata.has_valid_confirmation()
            assert not resp_instval.computing_metadata.has_valid_confirmation()
            # update local storage
            local_insts[inst] = resp_instval

        # Confirm headcounts
        time.sleep(1)
        assert local_insts
        for inst in local_insts:
            now = int(time.time())
            resp = ds_rc.request_seq(
                "POST",
                f"/institution/values/confirmation/{WBS_L1}",
                {
                    "institution": inst,
                    "headcounts": True,
                    "table": False,
                    # "computing": False,
                },
            )
            resp_instval = dacite.from_dict(uut.InstitutionValues, resp)
            assert any(
                resp_instval
                == dc.replace(
                    local_insts[inst],
                    headcounts_metadata=dc.replace(
                        resp_instval.headcounts_metadata, confirmation_ts=expected_ts
                    ),
                )
                for expected_ts in [now, now + 1]  # could be a bit slow
            )
            assert resp_instval.headcounts_metadata.has_valid_confirmation()
            assert not resp_instval.table_metadata.has_valid_confirmation()
            assert not resp_instval.computing_metadata.has_valid_confirmation()
            # update local storage
            local_insts[inst] = resp_instval

        # Confirm table + computing
        time.sleep(1)
        assert local_insts
        for inst in local_insts:
            now = int(time.time())
            resp = ds_rc.request_seq(
                "POST",
                f"/institution/values/confirmation/{WBS_L1}",
                {
                    "institution": inst,
                    "table": True,
                    "computing": True,
                },
            )
            resp_instval = dacite.from_dict(uut.InstitutionValues, resp)
            assert any(
                resp_instval
                == dc.replace(
                    local_insts[inst],
                    table_metadata=dc.replace(
                        resp_instval.table_metadata, confirmation_ts=expected_ts
                    ),
                    computing_metadata=dc.replace(
                        resp_instval.computing_metadata, confirmation_ts=expected_ts
                    ),
                )
                for expected_ts in [now, now + 1]  # could be a bit slow
            )
            assert resp_instval.headcounts_metadata.has_valid_confirmation()  # (before)
            assert resp_instval.table_metadata.has_valid_confirmation()
            assert resp_instval.computing_metadata.has_valid_confirmation()
            # update local storage
            local_insts[inst] = resp_instval

        # Re-touchstone
        time.sleep(1)
        ts_ts = ds_rc.request_seq(
            "POST", f"/institution/values/confirmation/touchstone/{WBS_L1}"
        )["touchstone_timestamp"]
        assert (
            ts_ts
            == ds_rc.request_seq(
                "GET", f"/institution/values/confirmation/touchstone/{WBS_L1}"
            )["touchstone_timestamp"]
        )

        # Check values / confirmations
        time.sleep(1)
        assert local_insts
        for inst in local_insts:
            resp = ds_rc.request_seq(
                "GET", f"/institution/values/{WBS_L1}", {"institution": inst}
            )
            resp_instval = dacite.from_dict(uut.InstitutionValues, resp)
            assert resp_instval == dc.replace(
                local_insts[inst],
                headcounts_metadata=dc.replace(
                    resp_instval.headcounts_metadata, confirmation_touchstone_ts=ts_ts
                ),
                table_metadata=dc.replace(
                    resp_instval.table_metadata, confirmation_touchstone_ts=ts_ts
                ),
                computing_metadata=dc.replace(
                    resp_instval.computing_metadata, confirmation_touchstone_ts=ts_ts
                ),
            )
            assert not resp_instval.headcounts_metadata.has_valid_confirmation()
            assert not resp_instval.table_metadata.has_valid_confirmation()
            assert not resp_instval.computing_metadata.has_valid_confirmation()
            # update local storage
            local_insts[inst] = resp_instval
