"""Routes handlers for the MoU REST API server interface."""


import json
import logging
from typing import Any

from rest_tools.server import RestHandler, handler  # type: ignore

from . import table_config as tc
from . import wbs
from .config import AUTH_PREFIX
from .utils import db_utils, types, utils

_WBS_L1_REGEX_VALUES = "|".join(wbs.WORK_BREAKDOWN_STRUCTURES.keys())


# -----------------------------------------------------------------------------


class BaseMoUHandler(RestHandler):  # type: ignore  # pylint: disable=W0223
    """BaseMoUHandler is a RestHandler for all MoU routes."""

    def initialize(  # pylint: disable=W0221
        self, db_client: db_utils.MoUMotorClient, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize a BaseMoUHandler object."""
        super().initialize(*args, **kwargs)
        self.dbms = db_client  # pylint: disable=W0201


# -----------------------------------------------------------------------------


class MainHandler(BaseMoUHandler):  # pylint: disable=W0223
    """MainHandler is a BaseMoUHandler that handles the root route."""

    ROUTE = r"/$"

    def get(self) -> None:
        """Handle GET."""
        self.write({})


# -----------------------------------------------------------------------------


class TableHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for a table."""

    ROUTE = rf"/table/data/(?P<wbs_l1>{_WBS_L1_REGEX_VALUES})$"

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["read", "write", "admin"])  # type: ignore
    async def get(self, wbs_l1: str) -> None:
        """Handle GET."""
        collection = self.get_argument("snapshot", "")

        institution = self.get_argument("institution", default=None)
        restore_id = self.get_argument("restore_id", default=None)
        labor = self.get_argument("labor", default=None)
        total_rows = self.get_argument("total_rows", default=False, type=bool)

        if restore_id:
            await self.dbms.restore_record(wbs_l1, restore_id)

        table = await self.dbms.get_table(
            wbs_l1, collection, labor=labor, institution=institution
        )

        # On-the-fly fields/rows
        for record in table:
            utils.add_on_the_fly_fields(record)
        if total_rows:
            table.extend(
                utils.get_total_rows(
                    wbs_l1,
                    table,
                    only_totals_w_data=labor or institution,
                    with_us_non_us=not institution,
                )
            )

        # sort
        table.sort(key=tc.sort_key)

        self.write({"table": table})

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["admin"])  # type: ignore
    async def post(self, wbs_l1: str) -> None:
        """Handle POST."""
        base64_file = self.get_argument("base64_file")
        filename = self.get_argument("filename")
        creator = self.get_argument("creator")

        # ingest
        prev_snap, curr_snap = await self.dbms.ingest_xlsx(
            wbs_l1, base64_file, filename, creator
        )

        # get info for snapshot(s)
        curr_snap_info = await self.dbms.get_snapshot_info(wbs_l1, curr_snap)
        prev_snap_info = None
        if prev_snap:
            prev_snap_info = await self.dbms.get_snapshot_info(wbs_l1, prev_snap)

        self.write(
            {
                "n_records": len(await self.dbms.get_table(wbs_l1)),
                "previous_snapshot": prev_snap_info,
                "current_snapshot": curr_snap_info,
            }
        )


# -----------------------------------------------------------------------------


class RecordHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for a record."""

    ROUTE = rf"/record/(?P<wbs_l1>{_WBS_L1_REGEX_VALUES})$"

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def post(self, wbs_l1: str) -> None:
        """Handle POST."""
        record = self.get_argument("record")
        editor = self.get_argument("editor")

        if inst := self.get_argument("institution", default=None):
            record[tc.INSTITUTION] = inst  # insert
        if labor := self.get_argument("labor", default=None):
            record[tc.LABOR_CAT] = labor  # insert
        if task := self.get_argument("task", default=None):
            record[tc.TASK_DESCRIPTION] = task  # insert

        record = utils.remove_on_the_fly_fields(record)
        record = await self.dbms.upsert_record(wbs_l1, record, editor)
        record = utils.add_on_the_fly_fields(record)

        self.write({"record": record})

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def delete(self, wbs_l1: str) -> None:
        """Handle DELETE."""
        record_id = self.get_argument("record_id")
        editor = self.get_argument("editor")

        record = await self.dbms.delete_record(wbs_l1, record_id, editor)

        self.write({"record": record})


# -----------------------------------------------------------------------------


class TableConfigHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for the table config dict."""

    ROUTE = r"/table/config$"

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["read", "write", "admin"])  # type: ignore
    async def get(self) -> None:
        """Handle GET."""
        table_config = {
            l1: {
                "columns": tc.get_columns(),
                "simple_dropdown_menus": tc.get_simple_dropdown_menus(l1),
                "institutions": tc.get_institutions_and_abbrevs(),
                "labor_categories": tc.get_labor_categories_and_abbrevs(),
                "conditional_dropdown_menus": tc.get_conditional_dropdown_menus(l1),
                "dropdowns": tc.get_dropdowns(l1),
                "numerics": tc.get_numerics(),
                "non_editables": tc.get_non_editables(),
                "hiddens": tc.get_hiddens(),
                "tooltips": tc.get_tooltips(),
                "widths": tc.get_widths(),
                "border_left_columns": tc.get_border_left_columns(),
                "page_size": tc.get_page_size(),
            }
            for l1 in wbs.WORK_BREAKDOWN_STRUCTURES.keys()
        }

        logging.debug("Table Config:\n%s", json.dumps(table_config, indent=4))

        self.write(table_config)


# -----------------------------------------------------------------------------


class SnapshotsHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for listing the snapshots."""

    ROUTE = rf"/snapshots/list/(?P<wbs_l1>{_WBS_L1_REGEX_VALUES})$"

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["read", "write", "admin"])  # type: ignore
    async def get(self, wbs_l1: str) -> None:
        """Handle GET."""
        is_admin = self.get_argument("is_admin", type=bool, default=False)

        timestamps = await self.dbms.list_snapshot_timestamps(
            wbs_l1, exclude_admin_snaps=not is_admin
        )
        timestamps.sort(reverse=True)

        snapshots = [await self.dbms.get_snapshot_info(wbs_l1, ts) for ts in timestamps]

        self.write({"snapshots": snapshots})


# -----------------------------------------------------------------------------


class MakeSnapshotHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for making snapshots."""

    ROUTE = rf"/snapshots/make/(?P<wbs_l1>{_WBS_L1_REGEX_VALUES})$"

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def post(self, wbs_l1: str) -> None:
        """Handle POST."""
        name = self.get_argument("name")
        creator = self.get_argument("creator")

        snap_ts = await self.dbms.snapshot_live_collection(wbs_l1, name, creator, False)
        snap_info = await self.dbms.get_snapshot_info(wbs_l1, snap_ts)

        self.write(snap_info)


# -----------------------------------------------------------------------------


class InstitutionValuesHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for making snapshots."""

    ROUTE = rf"/institution/values/(?P<wbs_l1>{_WBS_L1_REGEX_VALUES})$"

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def get(self, wbs_l1: str) -> None:
        """Handle GET."""
        institution = self.get_argument("institution")
        snapshot_timestamp = self.get_argument("snapshot_timestamp", "")

        vals = await self.dbms.get_institution_values(
            wbs_l1, snapshot_timestamp, institution
        )

        self.write(vals)

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def post(self, wbs_l1: str) -> None:
        """Handle POST."""
        institution = self.get_argument("institution")

        phds = self.get_argument("phds_authors", type=int, default=-1)
        faculty = self.get_argument("faculty", type=int, default=-1)
        sci = self.get_argument("scientists_post_docs", type=int, default=-1)
        grad = self.get_argument("grad_students", type=int, default=-1)
        cpus = self.get_argument("cpus", type=int, default=-1)
        gpus = self.get_argument("gpus", type=int, default=-1)
        text = self.get_argument("text", default="")
        headcounts_confirmed = self.get_argument(
            "headcounts_confirmed", type=bool, default=False
        )
        computing_confirmed = self.get_argument(
            "computing_confirmed", type=bool, default=False
        )

        vals: types.InstitutionValues = {
            "phds_authors": phds if phds >= 0 else None,
            "faculty": faculty if faculty >= 0 else None,
            "scientists_post_docs": sci if sci >= 0 else None,
            "grad_students": grad if grad >= 0 else None,
            "cpus": cpus if cpus >= 0 else None,
            "gpus": gpus if gpus >= 0 else None,
            "text": text,
            "headcounts_confirmed": headcounts_confirmed,
            "computing_confirmed": computing_confirmed,
        }

        await self.dbms.upsert_institution_values(wbs_l1, institution, vals)

        self.write({})
