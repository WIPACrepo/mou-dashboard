"""Routes handlers for the MoU REST API server interface."""


from copy import deepcopy
from typing import Any, Optional

import pandas as pd  # type: ignore[import]
import tornado.web

# local imports
from keycloak_setup.icecube_setup import ICECUBE_INSTS  # type: ignore[import]
from rest_tools.client.json_util import json_decode  # type: ignore
from rest_tools.server import handler, RestHandler  # type: ignore

from . import table_config
from .config import MOU_AUTH_PREFIX

_ID = "id"
# read data from excel file
_TABLE = pd.read_excel("WBS.xlsx").fillna("")
_TABLE = [r for r in _TABLE.to_dict("records") if any(r.values())]
_TABLE = {f"Z{r[_ID]}": r for r in _TABLE}
for key in _TABLE.keys():
    _TABLE[key][_ID] = key


_WBS_L2 = "WBS L2"
_WBS_L3 = "WBS L3"
_LABOR_CAT = "Labor Cat."
_US_NON_US = "US / Non-US"
_INSTITUTION = "Institution"
_NAMES = "Names"
_TASKS = "Tasks"
_SOURCE_OF_FUNDS_US_ONLY = "Source of Funds (U.S. Only)"
_FTE = "FTE"
_NSF_MO_CORE = "NSF M&O Core"
_NSF_BASE_GRANTS = "NSF Base Grants"
_US_INSTITUTIONAL_IN_KIND = "U.S. Institutional In-Kind"
_EUROPE_ASIA_PACIFIC_IN_KIND = "Europe & Asia Pacific In-Kind"
_GRAND_TOTAL = "Grand Total"


_US = "US"
_NON_US = "Non-US"


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

        table = list(deepcopy(_TABLE).values())  # very important to deep-copy here

        # filter by labor
        if labor:
            table = [r for r in table if r[_LABOR_CAT] == labor]

        # filter by institution
        if institution:
            table = [r for r in table if r[_INSTITUTION] == institution]

        def _us_or_non_us(institution: str) -> str:
            for inst in ICECUBE_INSTS.values():
                if inst["abbreviation"] == institution:
                    if inst["is_US"]:
                        return _US
                    return _NON_US
            return ""

        # don't use US/Non-US from excel b/c later this won't even be stored in the DB
        for record in table:
            record[_US_NON_US] = _us_or_non_us(record[_INSTITUTION])

        for record in table:
            for field in record.keys():
                if record[field] is None:
                    record[field] = ""

        # sort
        table.sort(
            key=lambda k: (
                k[_WBS_L2],
                k[_WBS_L3],
                k[_US_NON_US],
                k[_INSTITUTION],
                k[_LABOR_CAT],
                k[_NAMES],
                k[_SOURCE_OF_FUNDS_US_ONLY],
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
            record[_INSTITUTION] = inst
        if labor := self.get_argument("labor", default=None):
            record[_LABOR_CAT] = labor

        # New
        if not record[_ID] and record[_ID] != 0:
            record[_ID] = _next_id()
            _TABLE[record[_ID]] = record  # add
            print(f"PUSHED NEW {record[_ID]} --- table now has {len(_TABLE)} entries")

        # Changed
        else:
            print(f"PUSHED {record[_ID]}")
            _TABLE[record[_ID]] = record  # replace record

        self.write({"record": record})

    # FIXME: figure out why auth isn't working
    # @handler.scope_role_auth(prefix=MOU_AUTH_PREFIX, roles=["web"])  # type: ignore
    def delete(self) -> None:
        """Handle DELETE."""
        record = self.get_argument("record")
        # try:
        del _TABLE[record[_ID]]
        print(f"DELETED {record[_ID]} --- table now has {len(_TABLE)} entries")
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
                # pylint: disable=W0212
                "columns": table_config._COLUMNS,
                "simple_dropdown_menus": table_config._SIMPLE_DROPDOWN_MENUS,
                "institutions": table_config._SIMPLE_DROPDOWN_MENUS[_INSTITUTION],
                "labor_categories": table_config._SIMPLE_DROPDOWN_MENUS[_LABOR_CAT],
                "conditional_dropdown_menus": table_config._CONDITIONAL_DROPDOWN_MENUS,
                "dropdowns": table_config._DROPDOWNS,
                "numerics": table_config._NUMERICS,
                "non_editables": table_config._NON_EDITABLES,
                "hiddens": table_config._HIDDENS,
                "widths": table_config._WIDTHS,
                "border_left_columns": table_config._BORDER_LEFT_COLUMNS,
                "page_size": table_config._PAGE_SIZE,
            }
        )


# -----------------------------------------------------------------------------
