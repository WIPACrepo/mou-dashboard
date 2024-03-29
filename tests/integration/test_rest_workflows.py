"""Integration test rest_server module.

NOTE: THESE TESTS NEED TO RUN IN ORDER -- STATE DEPENDENT
"""


# pylint: disable=W0212,W0621


import base64
import dataclasses as dc
import os
import random
import re
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

match os.getenv("INTEGRATION_TEST_INGEST_TYPE"):
    case "xlsx":
        SNAPSHOTS_DURING_INGESTION = 3
    case "mongodump_v2":
        SNAPSHOTS_DURING_INGESTION = 2
    case "mongodump_v3":
        SNAPSHOTS_DURING_INGESTION = 3
    case other:
        raise RuntimeError(
            f"did not receive valid 'INTEGRATION_TEST_INGEST_TYPE': {other}"
        )

with open("./tests/integration/Dummy_WBS.xlsx", "rb") as f:
    INITIAL_INGEST_BODY = {
        "base64_file": base64.b64encode(f.read()).decode(encoding="utf-8"),
        "filename": f.name,
        "creator": "Hank",
        "is_admin": True,
        "include_snapshot_info": True,
    }


# NOTE: EXECUTED FIRST SO OTHER TESTS HAVE DATA IN THE DB
def test_ingest(ds_rc: RestClient) -> None:
    """Test POST /table/data."""
    match os.getenv("INTEGRATION_TEST_INGEST_TYPE"):
        case "xlsx":
            # starting state is empty
            with pytest.raises(
                requests.exceptions.HTTPError,
                match=re.escape(
                    "422 Client Error: Snapshot Database has no collections (wbs_db='mo'). for url: http://localhost:8080/table/data/mo?is_admin=True"
                ),
            ):
                ds_rc.request_seq(
                    "GET",
                    f"/table/data/{WBS_L1}",
                    {"is_admin": True, "include_snapshot_info": True},
                )
            # ingest -- gets a snapshot
            resp_post = ds_rc.request_seq(
                "POST", f"/table/data/{WBS_L1}", INITIAL_INGEST_BODY
            )
            assert not resp_post["previous_snapshot"]
            # snaps
            snaps = ds_rc.request_seq(
                "GET",
                f"/snapshots/list/{WBS_L1}",
                {"is_admin": True, "include_snapshot_info": True},
            )["snapshots"]
            assert len(snaps) == 1
            # get only snap
            snap_resp = ds_rc.request_seq(
                "GET",
                f"/table/data/{WBS_L1}",
                {
                    "is_admin": True,
                    "include_snapshot_info": True,
                    "snapshot": snaps[0]["timestamp"],
                },
            )
            assert not snap_resp["previous_snapshot"]
            assert snap_resp["current_snapshot"] == snaps[0]
            for inst in set(r["Institution"] for r in snap_resp["table"]):
                ds_rc.request_seq(
                    "GET", f"/institution/values/{WBS_L1}", {"institution": inst}
                )
            # get live
            resp_live = ds_rc.request_seq(
                "GET",
                f"/table/data/{WBS_L1}",
                {"is_admin": True, "include_snapshot_info": True},
            )
            assert resp_live["previous_snapshot"]
            assert resp_live["previous_snapshot"] == snaps[0]
            for inst in set(r["Institution"] for r in resp_live["table"]):
                ds_rc.request_seq(
                    "GET", f"/institution/values/{WBS_L1}", {"institution": inst}
                )
        case "mongodump_v2":
            # CI runner should have pre-ingested 1 collection (only v2 data)
            # snaps -- none
            snaps = ds_rc.request_seq(
                "GET", f"/snapshots/list/{WBS_L1}", {"is_admin": True}
            )["snapshots"]
            assert len(snaps) == 0
            # get live
            resp_live = ds_rc.request_seq(
                "GET",
                f"/table/data/{WBS_L1}",
                {"is_admin": True, "include_snapshot_info": True},
            )
            assert not resp_live["previous_snapshot"]
            for inst in set(r["Institution"] for r in resp_live["table"]):
                ds_rc.request_seq(
                    "GET", f"/institution/values/{WBS_L1}", {"institution": inst}
                )
        case "mongodump_v3":
            # CI runner should have pre-ingested 2 collections (v2 + v3 data)
            # snaps
            snaps = ds_rc.request_seq(
                "GET",
                f"/snapshots/list/{WBS_L1}",
                {"is_admin": True},
            )["snapshots"]
            assert len(snaps) == 1
            # get only snap
            snap_resp = ds_rc.request_seq(
                "GET",
                f"/table/data/{WBS_L1}",
                {
                    "is_admin": True,
                    "include_snapshot_info": True,
                    "snapshot": snaps[0]["timestamp"],
                },
            )
            assert not snap_resp["previous_snapshot"]
            for inst in set(r["Institution"] for r in snap_resp["table"]):
                ds_rc.request_seq(
                    "GET", f"/institution/values/{WBS_L1}", {"institution": inst}
                )
            # get live
            resp_live = ds_rc.request_seq(
                "GET",
                f"/table/data/{WBS_L1}",
                {"is_admin": True, "include_snapshot_info": True},
            )
            assert resp_live["previous_snapshot"]
            assert resp_live["previous_snapshot"] == snaps[0]
            for inst in set(r["Institution"] for r in resp_live["table"]):
                ds_rc.request_seq(
                    "GET", f"/institution/values/{WBS_L1}", {"institution": inst}
                )
        case other:
            raise RuntimeError(
                f"did not receive valid 'INTEGRATION_TEST_INGEST_TYPE': {other}"
            )

    assert resp_live["n_records"]
    assert resp_live["current_snapshot"]["timestamp"] == "LIVE_COLLECTION"

    # Do it again...
    resp = ds_rc.request_seq("POST", f"/table/data/{WBS_L1}", INITIAL_INGEST_BODY)

    assert resp["n_records"]
    assert resp["previous_snapshot"]
    assert resp["current_snapshot"]
    assert float(resp["previous_snapshot"]["timestamp"]) < float(
        resp["current_snapshot"]["timestamp"]
    )

    # Now fail...
    with pytest.raises(requests.exceptions.HTTPError):
        resp = ds_rc.request_seq(
            "POST",
            f"/table/data/{WBS_L1}",
            {
                "base64_file": "123456789",
                "filename": "foo-file",
                "is_admin": True,
                "include_snapshot_info": True,
            },
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
        snaps = ds_rc.request_seq(
            "GET", f"/snapshots/list/{WBS_L1}", {"is_admin": True}
        )["snapshots"]
        assert len(snaps) == SNAPSHOTS_DURING_INGESTION
        # BUT some of those snaps were admin-only
        ingest_admin_only_snapshots = len([s for s in snaps if s["admin_only"]])
        ingest_nonadmin_snapshots = len(snaps) - ingest_admin_only_snapshots

        for i in range(ingest_nonadmin_snapshots + 1, 20):
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
                assert len(snapshots) == i + ingest_admin_only_snapshots
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
        tests: dict[str, dict[str, Any]] = {}
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
        for record in ds_rc.request_seq("GET", f"/table/data/{WBS_L1}", {})["table"]:
            self._assert_schema(record)

        # assert schema in Snapshot Collections
        for snapshot in ds_rc.request_seq(
            "GET", f"/snapshots/list/{WBS_L1}", {"is_admin": True}
        )["snapshots"]:
            resp = ds_rc.request_seq(
                "GET",
                f"/table/data/{WBS_L1}",
                {"snapshot": snapshot["timestamp"]},
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
        original_insts: dict[str, uut.InstitutionValues] = {}

        # Get values
        for inst in ["LBNL", "DESY", "Alberta"]:
            resp = ds_rc.request_seq(
                "GET",
                f"/institution/values/{WBS_L1}",
                {"institution": inst, "is_admin": True},
            )
            resp_instval = dacite.from_dict(uut.InstitutionValues, resp)
            if not (  # is this from the json test data?
                resp_instval.headcounts_metadata.last_edit_ts
                <= int(time.time()) - 60 * 60 * 24 * 3  # from test data
                and resp_instval.headcounts_metadata.confirmation_ts
                <= int(time.time()) - 60 * 60 * 24 * 3  # from test data
                and resp_instval.table_metadata.last_edit_ts
                <= int(time.time()) - 60 * 60 * 24 * 3  # from test data
                and resp_instval.table_metadata.confirmation_ts
                <= int(time.time()) - 60 * 60 * 24 * 3  # from test data
                and resp_instval.computing_metadata.last_edit_ts
                <= int(time.time()) - 60 * 60 * 24 * 3  # from test data
                and resp_instval.computing_metadata.confirmation_ts
                <= int(time.time()) - 60 * 60 * 24 * 3  # from test data
            ):
                # if it's not from the json test data, assert everything's confirmed by default
                assert resp_instval == uut.InstitutionValues()
                assert resp_instval.headcounts_metadata.has_valid_confirmation()
                assert resp_instval.table_metadata.has_valid_confirmation()
                assert resp_instval.computing_metadata.has_valid_confirmation()
            # update local storage
            original_insts[inst] = resp_instval

        # Add institution values
        time.sleep(1)
        assert original_insts
        for i, inst in enumerate(original_insts):
            post_instval = uut.InstitutionValues(
                phds_authors=random.randint(1, 10) * (i + 1),
                faculty=random.randint(1, 10) * (i + 1),
                scientists_post_docs=random.randint(1, 10) * (i + 1),
                grad_students=random.randint(1, 10) * (i + 1),
                cpus=random.randint(1, 10) * (i + 1),
                gpus=random.randint(1, 10) * (i + 1),
                text=f"{i}'s test text",
            )

            og_table_confirmation_state = dacite.from_dict(
                uut.InstitutionValues,
                ds_rc.request_seq(
                    "GET",
                    f"/institution/values/{WBS_L1}",
                    {"institution": inst, "is_admin": True},
                ),
            ).table_metadata.has_valid_confirmation()

            now = int(time.time())
            resp_instval = dacite.from_dict(
                uut.InstitutionValues,
                ds_rc.request_seq(
                    "POST",
                    f"/institution/values/{WBS_L1}",
                    post_instval.restful_dict(inst),
                ),
            )
            assert abs(now - int(time.time())) <= 1
            assert resp_instval == dc.replace(
                post_instval,
                # use copies of known metadata + assert last_edit_ts
                headcounts_metadata=dc.replace(
                    resp_instval.headcounts_metadata,
                    last_edit_ts=now,
                ),
                table_metadata=resp_instval.table_metadata,
                computing_metadata=dc.replace(
                    resp_instval.computing_metadata,
                    last_edit_ts=now,
                ),
            ) or resp_instval == dc.replace(  # could be a bit slow
                post_instval,
                # use copies of known metadata
                headcounts_metadata=dc.replace(
                    resp_instval.headcounts_metadata,
                    last_edit_ts=now + 1,
                ),
                table_metadata=resp_instval.table_metadata,
                computing_metadata=dc.replace(
                    resp_instval.computing_metadata,
                    last_edit_ts=now + 1,
                ),
            )
            assert not resp_instval.headcounts_metadata.has_valid_confirmation()
            assert (
                og_table_confirmation_state
                == resp_instval.table_metadata.has_valid_confirmation()
            )
            assert not resp_instval.computing_metadata.has_valid_confirmation()
            # update local storage
            original_insts[inst] = resp_instval

        # TEST EDITING TABLE
        time.sleep(1)
        assert original_insts
        for inst in original_insts:
            records = ds_rc.request_seq(
                "GET", f"/table/data/{WBS_L1}", {"institution": inst}
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
            assert resp_instval == dc.replace(
                original_insts[inst],
                table_metadata=dc.replace(
                    resp_instval.table_metadata,
                    last_edit_ts=now,
                ),
            ) or resp_instval == dc.replace(  # could be a bit slow
                original_insts[inst],
                table_metadata=dc.replace(
                    resp_instval.table_metadata,
                    last_edit_ts=now + 1,
                ),
            )
            assert not resp_instval.headcounts_metadata.has_valid_confirmation()
            assert not resp_instval.table_metadata.has_valid_confirmation()
            assert not resp_instval.computing_metadata.has_valid_confirmation()
            # update local storage
            original_insts[inst] = resp_instval

        # Confirm headcounts
        time.sleep(1)
        assert original_insts
        for inst in original_insts:
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
            assert resp_instval == dc.replace(
                original_insts[inst],
                headcounts_metadata=dc.replace(
                    resp_instval.headcounts_metadata,
                    confirmation_ts=now,
                ),
            ) or resp_instval == dc.replace(  # could be a bit slow
                original_insts[inst],
                headcounts_metadata=dc.replace(
                    resp_instval.headcounts_metadata,
                    confirmation_ts=now + 1,
                ),
            )
            assert resp_instval.headcounts_metadata.has_valid_confirmation()
            assert not resp_instval.table_metadata.has_valid_confirmation()
            assert not resp_instval.computing_metadata.has_valid_confirmation()
            # update local storage
            original_insts[inst] = resp_instval

        # Confirm table + computing
        time.sleep(1)
        assert original_insts
        for inst in original_insts:
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
            assert resp_instval == dc.replace(
                original_insts[inst],
                table_metadata=dc.replace(
                    resp_instval.table_metadata,
                    confirmation_ts=now,
                ),
                computing_metadata=dc.replace(
                    resp_instval.computing_metadata,
                    confirmation_ts=now,
                ),
            ) or resp_instval == dc.replace(  # could be a bit slow
                original_insts[inst],
                table_metadata=dc.replace(
                    resp_instval.table_metadata,
                    confirmation_ts=now + 1,
                ),
                computing_metadata=dc.replace(
                    resp_instval.computing_metadata,
                    confirmation_ts=now + 1,
                ),
            )
            assert resp_instval.headcounts_metadata.has_valid_confirmation()  # (before)
            assert resp_instval.table_metadata.has_valid_confirmation()
            assert resp_instval.computing_metadata.has_valid_confirmation()
            # update local storage
            original_insts[inst] = resp_instval

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
        assert original_insts
        for inst in original_insts:
            resp = ds_rc.request_seq(
                "GET", f"/institution/values/{WBS_L1}", {"institution": inst}
            )
            resp_instval = dacite.from_dict(uut.InstitutionValues, resp)
            assert resp_instval == dc.replace(
                original_insts[inst],
                headcounts_metadata=dc.replace(
                    resp_instval.headcounts_metadata,
                    confirmation_touchstone_ts=ts_ts,
                ),
                table_metadata=dc.replace(
                    resp_instval.table_metadata,
                    confirmation_touchstone_ts=ts_ts,
                ),
                computing_metadata=dc.replace(
                    resp_instval.computing_metadata,
                    confirmation_touchstone_ts=ts_ts,
                ),
            )
            assert not resp_instval.headcounts_metadata.has_valid_confirmation()
            assert not resp_instval.table_metadata.has_valid_confirmation()
            assert not resp_instval.computing_metadata.has_valid_confirmation()
            # update local storage
            original_insts[inst] = resp_instval
