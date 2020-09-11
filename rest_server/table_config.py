"""Values for the table config."""


# local imports
from keycloak_setup.icecube_setup import ICECUBE_INSTS  # type: ignore[import]

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
