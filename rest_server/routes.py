"""Routes handlers for the MoU REST API server interface."""


from typing import Any, Optional

import tornado.web

# local imports
from rest_tools.client.json_util import json_decode  # type: ignore
from rest_tools.server import handler, RestHandler  # type: ignore

from . import table_config as tc
from .config import AUTH_PREFIX
from .utils import db_utils, utils

# -----------------------------------------------------------------------------


class NoDefualtValue:  # pylint: disable=R0903
    """Signal no default value, AKA argument is required."""


_NO_DEFAULT = NoDefualtValue()


def _cast(type_: Optional[type], val: Any) -> Any:
    """Cast `val` to `type_` type.

    Raise 400 if there's a ValueError.
    """
    if not type_:
        return val
    try:
        if (type_ == bool) and (val == "False"):
            return False
        return type_(val)
    except ValueError as e:
        raise tornado.web.HTTPError(400, reason=f"(ValueError) {e}")


# -----------------------------------------------------------------------------


class BaseMoUHandler(RestHandler):  # type: ignore  # pylint: disable=W0223
    """BaseMoUHandler is a RestHandler for all MoU routes."""

    def initialize(  # pylint: disable=W0221
        self, db_client: db_utils.MoUMotorClient, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize a BaseMoUHandler object."""
        super().initialize(*args, **kwargs)
        self.dbms = db_client  # pylint: disable=W0201

    def get_json_body_argument(
        self,
        name: str,
        default: Any = _NO_DEFAULT,
        strip: bool = True,
        type_: Optional[type] = None,
    ) -> Any:
        """Return the argument by JSON-decoding the request body."""
        if self.request.body:
            try:
                val = json_decode(self.request.body)[name]  # type: ignore[no-untyped-call]
                if strip and isinstance(val, tornado.util.unicode_type):
                    val = val.strip()
                return _cast(type_, val)
            except KeyError:
                # Required -> raise 400
                if isinstance(default, NoDefualtValue):
                    raise tornado.web.MissingArgumentError(name)

        # Else:
        # Optional / Default
        if type_:
            assert isinstance(default, type_) or (default is None)
        return _cast(type_, default)

    def get_argument(  # pylint: disable=W0221
        self,
        name: str,
        default: Any = _NO_DEFAULT,
        strip: bool = True,
        type_: Optional[type] = None,
    ) -> Any:
        """Return argument. If no default provided raise 400 if not present.

        Try from `self.get_json_body_argument()` first, then from
        `super().get_argument()`.
        """
        # If:
        # Required -> raise 400
        if isinstance(default, NoDefualtValue):
            # check JSON'd body arguments
            try:
                return _cast(type_, self.get_json_body_argument(name, strip=strip))
            except tornado.web.MissingArgumentError:
                pass
            # check query and body arguments
            try:
                return _cast(type_, super().get_argument(name, strip=strip))
            except tornado.web.MissingArgumentError as e:
                raise tornado.web.HTTPError(400, reason=e.log_message)

        # Else:
        # Optional / Default
        if type_:
            assert isinstance(default, type_) or (default is None)
        # check JSON'd body arguments  # pylint: disable=C0103
        j = self.get_json_body_argument(name, default=default, strip=strip, type_=type_)
        if j != default:
            return j
        # check query and body arguments
        return _cast(type_, super().get_argument(name, default=default, strip=strip))


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

    ROUTE = r"/table/data$"

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["read", "write", "admin"])  # type: ignore
    async def get(self) -> None:
        """Handle GET."""
        collection = self.get_argument("snapshot", "")
        institution = self.get_argument("institution", default=None)
        restore_id = self.get_argument("restore_id", default=None)
        labor = self.get_argument("labor", default=None)
        total_rows = self.get_argument("total_rows", default=False, type_=bool)

        if restore_id:
            await self.dbms.restore_record(restore_id)

        table = await self.dbms.get_table(
            collection, labor=labor, institution=institution
        )

        # On-the-fly fields/rows
        for record in table:
            utils.add_on_the_fly_fields(record)
        if total_rows:
            table.extend(
                utils.get_total_rows(table, only_totals_w_data=labor or institution)
            )

        # sort
        table.sort(key=tc.sort_key)

        self.write({"table": table})

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["admin"])  # type: ignore
    async def post(self) -> None:
        """Handle POST."""
        base64_file = self.get_argument("base64_file")
        filename = self.get_argument("filename")

        previous_snapshot, current_snapshot = await self.dbms.ingest_xlsx(
            base64_file, filename
        )

        self.write(
            {
                "n_records": len(await self.dbms.get_table()),
                "previous_snapshot": previous_snapshot,
                "current_snapshot": current_snapshot,
            }
        )


# -----------------------------------------------------------------------------


class RecordHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for a record."""

    ROUTE = r"/record$"

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def post(self) -> None:
        """Handle POST."""
        record = self.get_argument("record")
        if inst := self.get_argument("institution", default=None):
            record[tc.INSTITUTION] = inst  # insert
        if labor := self.get_argument("labor", default=None):
            record[tc.LABOR_CAT] = labor  # insert

        record = utils.remove_on_the_fly_fields(record)
        record = await self.dbms.upsert_record(record)

        self.write({"record": record})

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def delete(self) -> None:
        """Handle DELETE."""
        record_id = self.get_argument("record_id")

        await self.dbms.delete_record(record_id)

        self.write({})


# -----------------------------------------------------------------------------


class TableConfigHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for the table config dict."""

    ROUTE = r"/table/config$"

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["read", "write", "admin"])  # type: ignore
    async def get(self) -> None:
        """Handle GET."""
        # TODO: (goal) store timestamp and duration to cache most recent version from Smartsheet in DB

        self.write(
            {
                "columns": tc.get_columns(),
                "simple_dropdown_menus": tc.get_simple_dropdown_menus(),
                "institutions": tc.get_institutions_and_abbrevs(),
                "labor_categories": tc.get_labor_cats(),
                "conditional_dropdown_menus": tc.get_conditional_dropdown_menus(),
                "dropdowns": tc.get_dropdowns(),
                "numerics": tc.get_numerics(),
                "non_editables": tc.get_non_editables(),
                "hiddens": tc.get_hiddens(),
                "widths": tc.get_widths(),
                "border_left_columns": tc.get_border_left_columns(),
                "page_size": tc.get_page_size(),
            }
        )


# -----------------------------------------------------------------------------


class SnapshotsHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for listing the snapshots."""

    ROUTE = r"/snapshots/timestamps$"

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["read", "write", "admin"])  # type: ignore
    async def get(self) -> None:
        """Handle GET."""
        snapshots = await self.dbms.list_snapshot_timestamps()
        snapshots.sort(reverse=True)

        self.write({"timestamps": snapshots})


class MakeSnapshotHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for making snapshots."""

    ROUTE = r"/snapshots/make$"

    @handler.scope_role_auth(prefix=AUTH_PREFIX, roles=["write", "admin"])  # type: ignore
    async def post(self) -> None:
        """Handle POST."""
        snapshot = await self.dbms.snapshot_live_collection()

        self.write({"timestamp": snapshot})
