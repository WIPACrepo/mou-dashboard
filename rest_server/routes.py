"""Routes handlers for the MoU REST API server interface."""


from copy import deepcopy
from typing import Any, Optional

import pandas as pd  # type: ignore[import]
import tornado.web

# local imports
from rest_tools.client.json_util import json_decode  # type: ignore
from rest_tools.server import handler, RestHandler  # type: ignore

from . import table_config as tc
from .config import MOU_AUTH_PREFIX
from .utils import utils

# read data from excel file
_TABLE = pd.read_excel("WBS.xlsx").fillna("")
_TABLE = [r for r in _TABLE.to_dict("records") if any(r.values())]
_TABLE = {f"Z{r[tc.ID]}": r for r in _TABLE}
for key in _TABLE.keys():
    _TABLE[key][tc.ID] = key

# remove rows with "total" in them (case-insensitive)
copy = {}
for k, v in _TABLE.items():
    # pylint: disable=C0103
    skip = False
    for data in v.values():
        if isinstance(data, str) and ("TOTAL" in data.upper()):
            skip = True
    if not skip:
        copy[k] = v
_TABLE = copy


def _next_id() -> str:
    return f"{max(_TABLE.keys())}{max(_TABLE.keys())}"


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
        # self, motor_client: MotorClient, *args: Any, **kwargs: Any
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize a BaseMoUHandler object."""
        super().initialize(*args, **kwargs)

        # self.motor = MoUMotorClient(motor_client)  # pylint: disable=W0201

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
    def get(self) -> None:
        """Handle GET."""
        institution = self.get_argument("institution", default=None)
        labor = self.get_argument("labor", default=None)
        total_rows = self.get_argument("total_rows", default=False, type_=bool)

        table = list(deepcopy(_TABLE).values())  # very important to deep-copy here

        # filter by labor
        if labor:
            table = [r for r in table if r[tc.LABOR_CAT] == labor]

        # filter by institution
        if institution:
            table = [r for r in table if r[tc.INSTITUTION] == institution]

        for record in table:
            for field in record.keys():
                if record[field] is None:
                    record[field] = ""

        # On-the-fly fields/rows
        for record in table:
            utils.add_on_the_fly_fields(record)
        if total_rows:
            utils.add_total_rows(table)

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
    def post(self) -> None:
        """Handle POST."""
        record = self.get_argument("record")
        if inst := self.get_argument("institution", default=None):
            record[tc.INSTITUTION] = inst
        if labor := self.get_argument("labor", default=None):
            record[tc.LABOR_CAT] = labor

        record = utils.remove_on_the_fly_fields(record)

        # New
        if not record[tc.ID] and record[tc.ID] != 0:
            record[tc.ID] = _next_id()
            _TABLE[record[tc.ID]] = record  # add
            print(f"PUSHED NEW {record[tc.ID]} --- table now has {len(_TABLE)} entries")

        # Changed
        else:
            print(f"PUSHED {record[tc.ID]}")
            _TABLE[record[tc.ID]] = record  # replace record

        self.write({"record": record})

    # FIXME: figure out why auth isn't working
    # @handler.scope_role_auth(prefix=MOU_AUTH_PREFIX, roles=["web"])  # type: ignore
    def delete(self) -> None:
        """Handle DELETE."""
        record = self.get_argument("record")
        # TODO: don't actually delete, just mark as deleted
        # try:
        del _TABLE[record[tc.ID]]
        print(f"DELETED {record[tc.ID]} --- table now has {len(_TABLE)} entries")
        # return True
        # except KeyError:
        #     print(f"couldn't delete {id_}")
        #     return False
        # raise tornado.web.HTTPError(400, reason=f"(Va")


# -----------------------------------------------------------------------------


class TableConfigHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for the table config dict."""

    # FIXME: figure out why auth isn't working
    # @handler.scope_role_auth(prefix=MOU_AUTH_PREFIX, roles=["web"])  # type: ignore
    async def get(self) -> None:
        """Handle GET."""
        # TODO: (short-term) grab these values from the db
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
