"""Routes handlers for the MOU REST API server interface."""


import dataclasses as dc
import json
import logging
from typing import Any

from motor.motor_tornado import MotorClient  # type: ignore
from rest_tools import server

from .config import AUTH_PREFIX, is_testing
from .data_sources import mou_db, table_config_cache, todays_institutions, wbs
from .utils import utils

_WBS_L1_REGEX_VALUES = "|".join(wbs.WORK_BREAKDOWN_STRUCTURES.keys())


# -----------------------------------------------------------------------------
# REST requestor auth


if is_testing():

    def scope_role_auth(**kwargs):  # type: ignore
        def make_wrapper(method):  # type: ignore[no-untyped-def]
            async def wrapper(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                logging.warning("TESTING: auth disabled")
                return await method(self, *args, **kwargs)

            return wrapper

        return make_wrapper

else:
    scope_role_auth = server.scope_role_auth

# -----------------------------------------------------------------------------


class BaseMOUHandler(server.RestHandler):  # pylint: disable=W0223
    """BaseMOUHandler is a RestHandler for all MOU routes."""

    def initialize(  # type: ignore[override]  # pylint: disable=W0221
        self,
        mongodb_url: str,
        tc_cache: table_config_cache.TableConfigCache,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize a BaseMOUHandler object."""
        super().initialize(*args, **kwargs)  # type: ignore[no-untyped-call]
        # pylint: disable=W0201
        self.tc_cache = tc_cache
        self.mou_db_client = mou_db.MOUDatabaseClient(
            MotorClient(mongodb_url), utils.MOUDataAdaptor(self.tc_cache)
        )
        self.tc_data_adaptor = utils.TableConfigDataAdaptor(self.tc_cache)


# -----------------------------------------------------------------------------


class MainHandler(BaseMOUHandler):  # pylint: disable=W0223
    """MainHandler is a BaseMOUHandler that handles the root route."""

    ROUTE = r"/$"

    def get(self) -> None:
        """Handle GET."""
        self.write({})


# -----------------------------------------------------------------------------


class TableHandler(BaseMOUHandler):  # pylint: disable=W0223
    """Handle requests for a table."""

    ROUTE = rf"/table/data/(?P<wbs_l1>{_WBS_L1_REGEX_VALUES})$"

    @scope_role_auth(prefix=AUTH_PREFIX, roles=["read", "write", "admin"])  # type: ignore
    async def get(self, wbs_l1: str) -> None:
        """Handle GET."""
        collection = self.get_argument(
            "snapshot",
            default="",
            type=str,
        )

        institution = self.get_argument(
            "institution",
            default="",
            type=str,
        )
        restore_id = self.get_argument(
            "restore_id",
            default="",
            type=str,
        )
        labor = self.get_argument(
            "labor",
            default="",
            type=str,
        )
        total_rows = self.get_argument(
            "total_rows",
            default=False,
            type=bool,
        )

        if restore_id:
            await self.mou_db_client.restore_record(wbs_l1, restore_id)

        table = await self.mou_db_client.get_table(
            wbs_l1, collection, labor=labor, institution=institution
        )

        # On-the-fly fields/rows
        for record in table:
            self.tc_data_adaptor.add_on_the_fly_fields(record)
        if total_rows:
            table.extend(
                self.tc_data_adaptor.get_total_rows(
                    wbs_l1,
                    table,
                    only_totals_w_data=bool(labor or institution),
                    with_us_non_us=not institution,
                )
            )

        # sort
        table.sort(key=self.tc_cache.sort_key)

        self.write({"table": table})

    @scope_role_auth(prefix=AUTH_PREFIX, roles=["admin"])  # type: ignore
    async def post(self, wbs_l1: str) -> None:
        """Handle POST."""
        base64_file = self.get_argument(
            "base64_file",
            type=str,
        )
        filename = self.get_argument(
            "filename",
            type=str,
        )
        creator = self.get_argument(
            "creator",
            type=str,
        )

        # ingest
        prev_snap, curr_snap = await self.mou_db_client.ingest_xlsx(
            wbs_l1, base64_file, filename, creator
        )

        # get info for snapshot(s)
        curr_snap_info = await self.mou_db_client.get_snapshot_info(wbs_l1, curr_snap)
        prev_snap_info = None
        if prev_snap:
            prev_snap_info = await self.mou_db_client.get_snapshot_info(
                wbs_l1, prev_snap
            )

        self.write(
            {
                "n_records": len(await self.mou_db_client.get_table(wbs_l1)),
                "previous_snapshot": dc.asdict(prev_snap_info) if prev_snap else None,
                "current_snapshot": dc.asdict(curr_snap_info),
            }
        )


# -----------------------------------------------------------------------------


class RecordHandler(BaseMOUHandler):  # pylint: disable=W0223
    """Handle requests for a record."""

    ROUTE = rf"/record/(?P<wbs_l1>{_WBS_L1_REGEX_VALUES})$"

    @scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def post(self, wbs_l1: str) -> None:
        """Handle POST."""
        record = self.get_argument(
            "record",
            type=dict,
        )
        editor = self.get_argument(
            "editor",
            type=str,
        )

        record = self.tc_data_adaptor.remove_on_the_fly_fields(record)
        record, instvals = await self.mou_db_client.upsert_record(
            wbs_l1, record, editor
        )
        record = self.tc_data_adaptor.add_on_the_fly_fields(record)
        resp = {"record": record}
        if instvals:
            resp["institution_values"] = dc.asdict(instvals)
        self.write(resp)

    @scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def delete(self, wbs_l1: str) -> None:
        """Handle DELETE."""
        record_id = self.get_argument(
            "record_id",
            type=str,
        )
        editor = self.get_argument(
            "editor",
            type=str,
        )

        record, instvals = await self.mou_db_client.delete_record(
            wbs_l1, record_id, editor
        )

        resp = {"record": record}
        if instvals:
            resp["institution_values"] = dc.asdict(instvals)
        self.write(resp)


# -----------------------------------------------------------------------------


class TableConfigHandler(BaseMOUHandler):  # pylint: disable=W0223
    """Handle requests for the table config dict."""

    ROUTE = r"/table/config$"

    @scope_role_auth(prefix=AUTH_PREFIX, roles=["read", "write", "admin"])  # type: ignore
    async def get(self) -> None:
        """Handle GET."""
        await self.tc_cache.refresh()
        table_config = {
            l1: {
                "columns": self.tc_cache.get_columns(),
                "simple_dropdown_menus": self.tc_cache.get_simple_dropdown_menus(l1),
                "labor_categories": self.tc_cache.get_labor_categories_and_abbrevs(),
                "conditional_dropdown_menus": self.tc_cache.get_conditional_dropdown_menus(
                    l1
                ),
                "dropdowns": self.tc_cache.get_dropdowns(l1),
                "numerics": self.tc_cache.get_numerics(),
                "non_editables": self.tc_cache.get_non_editables(),
                "hiddens": self.tc_cache.get_hiddens(),
                "mandatories": self.tc_cache.get_mandatory_columns(),
                "tooltips": self.tc_cache.get_tooltips(),
                "widths": self.tc_cache.get_widths(),
                "border_left_columns": self.tc_cache.get_border_left_columns(),
                "page_size": self.tc_cache.get_page_size(),
            }
            for l1 in wbs.WORK_BREAKDOWN_STRUCTURES.keys()  # pylint:disable=C0201
        }

        logging.debug(
            "Table Config Keys:\n%s",
            json.dumps({k: list(v.keys()) for k, v in table_config.items()}, indent=4),
        )

        self.write(table_config)


# -----------------------------------------------------------------------------


class SnapshotsHandler(BaseMOUHandler):  # pylint: disable=W0223
    """Handle requests for listing the snapshots."""

    ROUTE = rf"/snapshots/list/(?P<wbs_l1>{_WBS_L1_REGEX_VALUES})$"

    @scope_role_auth(prefix=AUTH_PREFIX, roles=["read", "write", "admin"])  # type: ignore
    async def get(self, wbs_l1: str) -> None:
        """Handle GET."""
        is_admin = self.get_argument(
            "is_admin",
            type=bool,
            default=False,
        )

        timestamps = await self.mou_db_client.list_snapshot_timestamps(
            wbs_l1, exclude_admin_snaps=not is_admin
        )
        timestamps.sort(reverse=True)

        snapshots = [
            await self.mou_db_client.get_snapshot_info(wbs_l1, ts) for ts in timestamps
        ]

        self.write({"snapshots": [dc.asdict(si) for si in snapshots]})


# -----------------------------------------------------------------------------


class MakeSnapshotHandler(BaseMOUHandler):  # pylint: disable=W0223
    """Handle requests for making snapshots."""

    ROUTE = rf"/snapshots/make/(?P<wbs_l1>{_WBS_L1_REGEX_VALUES})$"

    @scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def post(self, wbs_l1: str) -> None:
        """Handle POST."""
        name = self.get_argument(
            "name",
            type=str,
        )
        creator = self.get_argument(
            "creator",
            type=str,
        )

        snap_ts = await self.mou_db_client.snapshot_live_collection(
            wbs_l1, name, creator, False
        )
        snap_info = await self.mou_db_client.get_snapshot_info(wbs_l1, snap_ts)

        self.write(dc.asdict(snap_info))


# -----------------------------------------------------------------------------


class InstitutionValuesConfirmationTouchstoneHandler(
    BaseMOUHandler
):  # pylint: disable=W0223
    """Handle requests for making a new touchstone timestamp for institution
    values."""

    ROUTE = rf"/institution/values/confirmation/touchstone/(?P<wbs_l1>{_WBS_L1_REGEX_VALUES})$"

    @scope_role_auth(prefix=AUTH_PREFIX, roles=["admin"])  # type: ignore
    async def post(self, wbs_l1: str) -> None:
        """Handle POST."""
        timestamp = await self.mou_db_client.retouchstone(wbs_l1)

        self.write({"touchstone_timestamp": timestamp})

    @scope_role_auth(prefix=AUTH_PREFIX, roles=["admin"])  # type: ignore
    async def get(self, wbs_l1: str) -> None:
        """Handle POST."""
        timestamp = await self.mou_db_client.get_touchstone(wbs_l1)

        self.write({"touchstone_timestamp": timestamp})


# -----------------------------------------------------------------------------


class InstitutionValuesConfirmationHandler(BaseMOUHandler):  # pylint: disable=W0223
    """Handle requests for confirming institution values."""

    ROUTE = rf"/institution/values/confirmation/(?P<wbs_l1>{_WBS_L1_REGEX_VALUES})$"

    @scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def post(self, wbs_l1: str) -> None:
        """Handle POST."""
        institution = self.get_argument(
            "institution",
            type=str,
        )
        headcounts = self.get_argument(
            "headcounts",
            type=bool,
            default=False,
        )
        table = self.get_argument(
            "table",
            type=bool,
            default=False,
        )
        computing = self.get_argument(
            "computing",
            type=bool,
            default=False,
        )

        vals = await self.mou_db_client.confirm_institution_values(
            wbs_l1, institution, headcounts, table, computing
        )

        self.write(dc.asdict(vals))


# -----------------------------------------------------------------------------


class InstitutionValuesHandler(BaseMOUHandler):  # pylint: disable=W0223
    """Handle requests for managing an institution's values, possibly for a
    snapshot."""

    ROUTE = rf"/institution/values/(?P<wbs_l1>{_WBS_L1_REGEX_VALUES})$"

    @scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def get(self, wbs_l1: str) -> None:
        """Handle GET."""
        institution = self.get_argument(
            "institution",
            type=str,
        )
        snapshot_timestamp = self.get_argument(
            "snapshot_timestamp",
            default="",
            type=str,
        )

        vals = await self.mou_db_client.get_institution_values(
            wbs_l1, snapshot_timestamp, institution
        )

        self.write(dc.asdict(vals))

    @scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def post(self, wbs_l1: str) -> None:
        """Handle POST."""
        institution = self.get_argument(
            "institution",
            type=str,
        )

        # client cannot try to override metadata
        phds_authors = self.get_argument(
            "phds_authors",
            type=int,
            default=-1,
        )
        faculty = self.get_argument(
            "faculty",
            type=int,
            default=-1,
        )
        scientists_post_docs = self.get_argument(
            "scientists_post_docs",
            type=int,
            default=-1,
        )
        grad_students = self.get_argument(
            "grad_students",
            type=int,
            default=-1,
        )
        cpus = self.get_argument(
            "cpus",
            type=int,
            default=-1,
        )
        gpus = self.get_argument(
            "gpus",
            type=int,
            default=-1,
        )
        text = self.get_argument(
            "text",
            default="",
            type=str,
        )

        vals = await self.mou_db_client.upsert_institution_values(
            wbs_l1,
            institution,
            None if phds_authors == -1 else phds_authors,
            None if faculty == -1 else faculty,
            None if scientists_post_docs == -1 else scientists_post_docs,
            None if grad_students == -1 else grad_students,
            None if cpus == -1 else cpus,
            None if gpus == -1 else gpus,
            text,
        )

        self.write(dc.asdict(vals))


# -----------------------------------------------------------------------------


class InstitutionStaticHandler(BaseMOUHandler):  # pylint: disable=W0223
    """Handle requests for querying current-day info about the institutions."""

    ROUTE = r"/institution/today$"

    @scope_role_auth(prefix=AUTH_PREFIX, roles=["read", "write", "admin"])  # type: ignore
    async def get(self) -> None:
        """Handle GET."""
        institutions = await todays_institutions.request_krs_institutions()
        vals = {i.short_name: dc.asdict(i) for i in institutions}

        self.write(vals)
