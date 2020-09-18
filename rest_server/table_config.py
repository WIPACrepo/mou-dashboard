"""Values for the table config."""


# local imports
from keycloak_setup.icecube_setup import ICECUBE_INSTS  # type: ignore[import]

ID = "_id"
WBS_L2 = "WBS L2"
WBS_L3 = "WBS L3"
LABOR_CAT = "Labor Cat."
US_NON_US = "US / Non-US"
INSTITUTION = "Institution"
NAMES = "Names"
_TASKS = "Tasks"
SOURCE_OF_FUNDS_US_ONLY = "Source of Funds (U.S. Only)"
FTE = "FTE"
NSF_MO_CORE = "NSF M&O Core"
NSF_BASE_GRANTS = "NSF Base Grants"
US_IN_KIND = "US In-Kind"
NON_US_IN_KIND = "Non-US In-Kind"
GRAND_TOTAL = "Grand Total"
TOTAL_COL = "Total Of?"


US = "US"
NON_US = "Non-US"


COLUMNS = [
    ID,
    WBS_L2,
    WBS_L3,
    US_NON_US,
    INSTITUTION,
    LABOR_CAT,
    NAMES,
    _TASKS,
    SOURCE_OF_FUNDS_US_ONLY,
    FTE,
    TOTAL_COL,
    NSF_MO_CORE,
    NSF_BASE_GRANTS,
    US_IN_KIND,
    NON_US_IN_KIND,
    GRAND_TOTAL,
]

FUNDING_SOURCES = [
    NSF_MO_CORE,
    NSF_BASE_GRANTS,
    US_IN_KIND,
    NON_US_IN_KIND,
]

L2_CATEGORIES = [
    "2.1 Program Coordination",
    "2.2 Detector Operations & Maintenance (Online)",
    "2.3 Computing & Data Management Services",
    "2.4 Data Processing & Simulation Services",
    "2.5 Software",
    "2.6 Calibration",
]

L3_CATEGORIES_BY_L2 = {
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
}

SIMPLE_DROPDOWN_MENUS = {
    WBS_L2: L2_CATEGORIES,
    LABOR_CAT: sorted(
        ["AD", "CS", "DS", "EN", "GR", "IT", "KE", "MA", "PO", "SC", "WO"]
    ),
    INSTITUTION: sorted(inst["abbreviation"] for inst in ICECUBE_INSTS.values()),
}


CONDITIONAL_DROPDOWN_MENUS = {
    WBS_L3: (WBS_L2, L3_CATEGORIES_BY_L2),
    SOURCE_OF_FUNDS_US_ONLY: (
        US_NON_US,
        {US: [NSF_MO_CORE, NSF_BASE_GRANTS, US_IN_KIND], NON_US: [NON_US_IN_KIND]},
    ),
}


DROPDOWNS = list(SIMPLE_DROPDOWN_MENUS.keys()) + list(CONDITIONAL_DROPDOWN_MENUS.keys())


NUMERICS = [FTE, GRAND_TOTAL] + FUNDING_SOURCES


NON_EDITABLES = [ID, US_NON_US, GRAND_TOTAL, TOTAL_COL] + FUNDING_SOURCES
HIDDENS = NON_EDITABLES


WIDTHS = {
    ID: 100,
    WBS_L2: 350,
    WBS_L3: 300,
    US_NON_US: 100,
    LABOR_CAT: 125,
    INSTITUTION: 140,
    NAMES: 150,
    _TASKS: 300,
    SOURCE_OF_FUNDS_US_ONLY: 185,
    FTE: 90,
    NSF_MO_CORE: 110,
    NSF_BASE_GRANTS: 110,
    US_IN_KIND: 110,
    NON_US_IN_KIND: 110,
    GRAND_TOTAL: 110,
    TOTAL_COL: 400,
}


BORDER_LEFT_COLUMNS = [
    US_NON_US,
    INSTITUTION,
    SOURCE_OF_FUNDS_US_ONLY,
    TOTAL_COL,
    GRAND_TOTAL,
]


PAGE_SIZE = 15


ON_THE_FLY_FIELDS = [
    US_NON_US,
    NSF_MO_CORE,
    NSF_BASE_GRANTS,
    US_IN_KIND,
    NON_US_IN_KIND,
    GRAND_TOTAL,
    TOTAL_COL,
]
