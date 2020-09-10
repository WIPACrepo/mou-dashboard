"""Routes handlers for the MoU REST API server interface."""


from typing import Any, Optional

import tornado.web

# local imports
from keycloak_setup.icecube_setup import ICECUBE_INSTS  # type: ignore[import]
from rest_tools.client.json_util import json_decode  # type: ignore
from rest_tools.server import handler, RestHandler  # type: ignore

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


_ID = "id"
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


_COLUMNS = [
    _ID,
    _WBS_L2,
    _WBS_L3,
    _US_NON_US,
    _INSTITUTION,
    _LABOR_CAT,
    _NAMES,
    _TASKS,
    _SOURCE_OF_FUNDS_US_ONLY,
    _FTE,
    _NSF_MO_CORE,
    _NSF_BASE_GRANTS,
    _US_INSTITUTIONAL_IN_KIND,
    _EUROPE_ASIA_PACIFIC_IN_KIND,
    _GRAND_TOTAL,
]


_SIMPLE_DROPDOWN_MENUS = {
    _WBS_L2: [
        "2.1 Program Coordination",
        "2.2 Detector Operations & Maintenance (Online)",
        "2.3 Computing & Data Management Services",
        "2.4 Data Processing & Simulation Services",
        "2.5 Software",
        "2.6 Calibration",
    ],
    _LABOR_CAT: sorted(
        ["AD", "CS", "DS", "EN", "GR", "IT", "KE", "MA", "PO", "SC", "WO"]
    ),
    _INSTITUTION: sorted(inst["abbreviation"] for inst in ICECUBE_INSTS.values()),
}

_CONDITIONAL_DROPDOWN_MENUS = {
    _WBS_L3: (
        _WBS_L2,
        {
            "2.1 Program Coordination": [
                "2.1.0 Program Coordination",
                "2.1.1 Administration",
                "2.1.2 Engineering and R&D Support",
                "2.1.3 USAP Support & Safety",
                "2.1.4 Education & Outreach",
                "2.1.5 Communications",
            ],
            "2.2 Detector Operations & Maintenance (Online)": [
                "2.2.0 Detector Operations & Maintenance",
                "2.2.1 Run Coordination",
                "2.2.2 Data Acquisition",
                "2.2.3 Online Filter (PnF)",
                "2.2.4 Detector Monitoring",
                "2.2.5 Experiment Control",
                "2.2.6 Surface Detectors",
                "2.2.7 Supernova System",
                "2.2.8 Real-Time Alerts",
                "2.2.9 SPS/SPTS",
            ],
            "2.3 Computing & Data Management Services": [
                "2.3.0 Computing & Data Management Services",
                "2.3.1 Data Storage & Transfer",
                "2.3.2 Core Data Center Infrastructure",
                "2.3.3 Central Computing Resources",
                "2.3.4 Distributed Computing Resources",
            ],
            "2.4 Data Processing & Simulation Services": [
                "2.4.0 Data Processing & Simulation Services",
                "2.4.1 Offline Data Production",
                "2.4.2 Simulation Production",
                "2.4.3 Public Data Products",
            ],
            "2.5 Software": [
                "2.5.0 Software",
                "2.5.1 Core Software",
                "2.5.2 Simulation Software",
                "2.5.3 Reconstruction",
                "2.5.4 Science Support Tools",
                "2.5.5 Software Development Infrastructure",
            ],
            "2.6 Calibration": [
                "2.6.0 Calibration",
                "2.6.1 Detector Calibration",
                "2.6.2 Ice Properties",
            ],
        },
    ),
    _SOURCE_OF_FUNDS_US_ONLY: (
        _US_NON_US,
        {
            _US: [_NSF_MO_CORE, "Base Grants", "US In-Kind"],
            _NON_US: ["Non-US In-kind"],
        },
    ),
}


_DROPDOWNS = list(_SIMPLE_DROPDOWN_MENUS.keys()) + list(
    _CONDITIONAL_DROPDOWN_MENUS.keys()
)


_NUMERICS = [
    _FTE,
    _NSF_MO_CORE,
    _NSF_BASE_GRANTS,
    _US_INSTITUTIONAL_IN_KIND,
    _EUROPE_ASIA_PACIFIC_IN_KIND,
    _GRAND_TOTAL,
]

_NON_EDITABLES = [
    _US_NON_US,
    _NSF_MO_CORE,
    _NSF_BASE_GRANTS,
    _US_INSTITUTIONAL_IN_KIND,
    _EUROPE_ASIA_PACIFIC_IN_KIND,
    _GRAND_TOTAL,
]

_HIDDENS = [
    _ID,
    _US_NON_US,
    _NSF_MO_CORE,
    _NSF_BASE_GRANTS,
    _US_INSTITUTIONAL_IN_KIND,
    _EUROPE_ASIA_PACIFIC_IN_KIND,
    _GRAND_TOTAL,
]

_WIDTHS = {
    _ID: 100,
    _WBS_L2: 350,
    _WBS_L3: 300,
    _US_NON_US: 100,
    _LABOR_CAT: 100,
    _INSTITUTION: 140,
    _NAMES: 150,
    _TASKS: 300,
    _SOURCE_OF_FUNDS_US_ONLY: 150,
    _FTE: 90,
    _NSF_MO_CORE: 110,
    _NSF_BASE_GRANTS: 110,
    _US_INSTITUTIONAL_IN_KIND: 110,
    _EUROPE_ASIA_PACIFIC_IN_KIND: 110,
    _GRAND_TOTAL: 110,
}


_BORDER_LEFT_COLUMNS = [
    _US_NON_US,
    _INSTITUTION,
    _SOURCE_OF_FUNDS_US_ONLY,
    _NSF_MO_CORE,
    _GRAND_TOTAL,
]

_PAGE_SIZE = 15


class TableConfigHandler(BaseMoUHandler):  # pylint: disable=W0223
    """Handle requests for the table config dict."""

    @handler.scope_role_auth(prefix=MOU_AUTH_PREFIX, roles=["web"])  # type: ignore
    async def get(self) -> None:
        """Handle GET."""
        self.write(
            {
                "columns": _COLUMNS,
                "simple_dropdown_menus": _SIMPLE_DROPDOWN_MENUS,
                "conditional_dropdown_menus": _CONDITIONAL_DROPDOWN_MENUS,
                "dropdowns": _DROPDOWNS,
                "numerics": _NUMERICS,
                "non_editables": _NON_EDITABLES,
                "hiddens": _HIDDENS,
                "widths": _WIDTHS,
                "border_left_columns": _BORDER_LEFT_COLUMNS,
                "page_size": _PAGE_SIZE,
            }
        )


# -----------------------------------------------------------------------------
