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
            return _cast(type_, super().get_argument(name, strip=strip))

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

    def get(self) -> None:
        """Handle GET."""
        self.write({})


# -----------------------------------------------------------------------------


class TableHandler(BaseMoUHandler):  # pylint: disable=W0223
    """MainHandler is a BaseMoUHandler that handles the root route."""

    # FIXME: figure out why auth isn't working
    # @handler.scope_role_auth(prefix=MOU_AUTH_PREFIX, roles=["web"])  # type: ignore
    async def get(self) -> None:
        """Handle GET."""
        collection = self.get_argument("snapshot", "")
        institution = self.get_argument("institution", default=None)
        labor = self.get_argument("labor", default=None)
        total_rows = self.get_argument("total_rows", default=False, type_=bool)

        table = await self.dbms.get_table(
            collection, labor=labor, institution=institution
        )

        # On-the-fly fields/rows
        for record in table:
            utils.add_on_the_fly_fields(record)
        if total_rows:
            utils.insert_total_rows(table)

        # sort
        max_str = "ZZZZ"  # HACK: this will sort empty/missing values last
        table.sort(
            key=lambda k: (
                k.get(tc.WBS_L2, max_str),
                k.get(tc.WBS_L3, max_str),
                k.get(tc.US_NON_US, max_str),
                k.get(tc.INSTITUTION, max_str),
                k.get(tc.LABOR_CAT, max_str),
                k.get(tc.NAMES, max_str),
                k.get(tc.SOURCE_OF_FUNDS_US_ONLY, max_str),
            ),
        )

        self.write({"table": table})


# -----------------------------------------------------------------------------


class RecordHandler(BaseMoUHandler):  # pylint: disable=W0223
    """MainHandler is a BaseMoUHandler that handles the root route."""

    # FIXME: figure out why auth isn't working
    # @handler.scope_role_auth(prefix=MOU_AUTH_PREFIX, roles=["web"])  # type: ignore
    async def post(self) -> None:
        """Handle POST."""
        collection = self.get_argument("snapshot", "")
        record = self.get_argument("record")
        if inst := self.get_argument("institution", default=None):
            record[tc.INSTITUTION] = inst  # insert
        if labor := self.get_argument("labor", default=None):
            record[tc.LABOR_CAT] = labor  # insert

        record = utils.remove_on_the_fly_fields(record)
        record = await self.dbms.upsert_record(record, collection=collection)

        self.write({"record": record})

    # FIXME: figure out why auth isn't working
    # @handler.scope_role_auth(prefix=MOU_AUTH_PREFIX, roles=["web"])  # type: ignore
    async def delete(self) -> None:
        """Handle DELETE."""
        collection = self.get_argument("snapshot", "")
        record = self.get_argument("record")

        await self.dbms.delete_record(record, collection=collection)

        self.write({})


# -----------------------------------------------------------------------------


class TableConfigHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for the table config dict."""

    # FIXME: figure out why auth isn't working
    # @handler.scope_role_auth(prefix=MOU_AUTH_PREFIX, roles=["web"])  # type: ignore
    async def get(self) -> None:
        """Handle GET."""
        # TODO: (short-term) grab these values from 'TableConfig' db
        # TODO: (goal) store timestamp and duration to cache most recent version from Smartsheet

        self.write(
            {
                "columns": tc.COLUMNS,
                "simple_dropdown_menus": tc.SIMPLE_DROPDOWN_MENUS,
                "institutions": tc.SIMPLE_DROPDOWN_MENUS[tc.INSTITUTION],
                "labor_categories": tc.SIMPLE_DROPDOWN_MENUS[tc.LABOR_CAT],
                "conditional_dropdown_menus": tc.CONDITIONAL_DROPDOWN_MENUS,
                "dropdowns": tc.DROPDOWNS,
                "numerics": tc.NUMERICS,
                "non_editables": tc.NON_EDITABLES,
                "hiddens": tc.HIDDENS,
                "widths": tc.WIDTHS,
                "border_left_columns": tc.BORDER_LEFT_COLUMNS,
                "page_size": tc.PAGE_SIZE,
            }
        )


# -----------------------------------------------------------------------------
