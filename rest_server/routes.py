"""Routes handlers for the MoU REST API server interface."""


from typing import Any, Optional

import tornado.web

# local imports
from rest_tools.client.json_util import json_decode  # type: ignore
from rest_tools.server import handler, RestHandler  # type: ignore

from . import table_config
from .config import MOU_AUTH_PREFIX

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
        # super().initialize(*args, **kwargs)

        # self.motor_client = motor_client  # pylint: disable=W0201
        # self.md_mc = MoUMotorClient(motor_client)  # pylint: disable=W0201

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


class TableConfigHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for the table config dict."""

    @handler.scope_role_auth(prefix=MOU_AUTH_PREFIX, roles=["web"])  # type: ignore
    async def get(self) -> None:
        """Handle GET."""
        # TODO: (short-term) grab these values from the db
        # TODO: (goal) store timestamp and duration to cache most recent version from Smartsheet

        self.write(
            {
                # pylint: disable=W0212
                "columns": table_config._COLUMNS,
                "simple_dropdown_menus": table_config._SIMPLE_DROPDOWN_MENUS,
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
