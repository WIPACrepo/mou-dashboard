"""REST interface for reading and writing MoU data."""


from copy import deepcopy
from typing import cast, List, Optional, Tuple

import pandas as pd  # type: ignore[import]

from .icecube_setup import ICECUBE_INSTS
from .types import Record, Table

# Constants
LABOR_CAT_LABEL = "Labor Cat."
INSTITUTION_LABEL = "Institution"


_ID = "id"
_WBS_L2 = "WBS L2"
_WBS_L3 = "WBS L3"
_US_NON_US = "US / Non-US"
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


# read data from excel file
_TABLE = pd.read_excel("WBS.xlsx").fillna("")
_TABLE = [r for r in _TABLE.to_dict("records") if any(r.values())]
_TABLE = {f"Z{r[_ID]}": r for r in _TABLE}
for key in _TABLE.keys():
    _TABLE[key][_ID] = key


# --------------------------------------------------------------------------------------
# Data/Table functions


def pull_data_table(institution: str = "", labor: str = "") -> Table:
    """Get table, optionally filtered by institution and/or labor."""
    table = list(deepcopy(_TABLE).values())  # very important to deep-copy here

    # filter by labor
    if labor:
        table = [r for r in table if r[LABOR_CAT_LABEL] == labor]

    # filter by institution
    if institution:
        table = [r for r in table if r[INSTITUTION_LABEL] == institution]

    def _us_or_non_us(institution: str) -> str:
        for inst in ICECUBE_INSTS.values():
            if inst["abbreviation"] == institution:
                if inst["is_US"]:
                    return _US
                return _NON_US
        return ""

    # don't use US/Non-US from excel b/c later this won't even be stored in the DB
    for record in table:
        record[_US_NON_US] = _us_or_non_us(record[INSTITUTION_LABEL])

    for record in table:
        for field in record.keys():
            if record[field] is None:
                record[field] = ""

    # sort
    table = sorted(
        table,
        key=lambda k: (
            k[_WBS_L2],
            k[_WBS_L3],
            k[_US_NON_US],
            k[INSTITUTION_LABEL],
            k[LABOR_CAT_LABEL],
            k[_NAMES],
            k[_SOURCE_OF_FUNDS_US_ONLY],
        ),
    )

    return cast(Table, table)


def _next_id() -> str:
    return f"{max(_TABLE.keys())}{max(_TABLE.keys())}"


def push_record(record: Record) -> Optional[Record]:
    """Push new/changed record to source."""
    # New
    if not record[_ID] and record[_ID] != 0:
        record[_ID] = _next_id()
        _TABLE[record[_ID]] = record  # add
        print(f"PUSHED NEW {record[_ID]} --- table now has {len(_TABLE)} entries")
        return record

    # Changed
    print(f"PUSHED {record[_ID]}")
    _TABLE[record[_ID]] = record  # replace record
    return record


def delete_record(record: Record) -> bool:
    """Delete the record, return True if successful."""
    # try:
    del _TABLE[record[_ID]]
    print(f"DELETED {record[_ID]} --- table now has {len(_TABLE)} entries")
    return True
    # except KeyError:
    #     print(f"couldn't delete {id_}")
    #     return False


# --------------------------------------------------------------------------------------
# Column functions

_COLUMNS = [
    _ID,
    _WBS_L2,
    _WBS_L3,
    _US_NON_US,
    INSTITUTION_LABEL,
    LABOR_CAT_LABEL,
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


def get_table_columns() -> List[str]:
    """Return table column's names."""
    return _COLUMNS


_SIMPLE_DROPDOWN_MENUS = {
    _WBS_L2: [
        "2.1 Program Coordination",
        "2.2 Detector Operations & Maintenance (Online)",
        "2.3 Computing & Data Management Services",
        "2.4 Data Processing & Simulation Services",
        "2.5 Software",
        "2.6 Calibration",
    ],
    LABOR_CAT_LABEL: sorted(
        ["AD", "CS", "DS", "EN", "GR", "IT", "KE", "MA", "PO", "SC", "WO"]
    ),
    INSTITUTION_LABEL: sorted(inst["abbreviation"] for inst in ICECUBE_INSTS.values()),
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


def get_simple_column_dropdown_menu(column: str) -> List[str]:
    """Return dropdown menu for a column."""
    return _SIMPLE_DROPDOWN_MENUS[column]


def get_institutions() -> List[str]:
    """Return list of institutions."""
    return get_simple_column_dropdown_menu(INSTITUTION_LABEL)


def get_labor_categories() -> List[str]:
    """Return list of labors."""
    return get_simple_column_dropdown_menu(LABOR_CAT_LABEL)


def is_column_dropdown(column: str) -> bool:
    """Return  whether column is a dropdown-type."""
    return column in _DROPDOWNS


def is_column_numeric(column: str) -> bool:
    """Return whether column takes numeric data."""
    return column in _NUMERICS


def is_column_editable(column: str) -> bool:
    """Return whether column data can be edited by end-user."""
    return column not in _NON_EDITABLES


def get_hidden_columns() -> List[str]:
    """Return the columns hidden be default."""
    return _HIDDENS


def get_dropdown_columns() -> List[str]:
    """Return list of dropdown-type columns."""
    return _DROPDOWNS


def is_simple_dropdown(column: str) -> bool:
    """Return whether column is a simple dropdown-type."""
    return column in _SIMPLE_DROPDOWN_MENUS.keys()


def is_conditional_dropdown(column: str) -> bool:
    """Return whether column is a conditional dropdown-type."""
    return column in _CONDITIONAL_DROPDOWN_MENUS.keys()


def get_conditional_column_dependee(column: str) -> Tuple[str, List[str]]:
    """Get the dependee column's (name and list of options)."""
    return (
        _CONDITIONAL_DROPDOWN_MENUS[column][0],
        list(_CONDITIONAL_DROPDOWN_MENUS[column][1].keys()),
    )


def get_conditional_column_dropdown_menu(
    column: str, dependee_column_option: str
) -> List[str]:
    """Get the dropdown menu for a conditional dropdown-column."""
    return _CONDITIONAL_DROPDOWN_MENUS[column][1][dependee_column_option]


_WIDTHS = {
    _ID: 100,
    _WBS_L2: 350,
    _WBS_L3: 300,
    _US_NON_US: 100,
    LABOR_CAT_LABEL: 85,
    INSTITUTION_LABEL: 140,
    _NAMES: 150,
    _TASKS: 300,
    _SOURCE_OF_FUNDS_US_ONLY: 150,
    _FTE: 90,
    _NSF_MO_CORE: 90,
    _NSF_BASE_GRANTS: 90,
    _US_INSTITUTIONAL_IN_KIND: 90,
    _EUROPE_ASIA_PACIFIC_IN_KIND: 90,
    _GRAND_TOTAL: 90,
}


def get_column_width(column: str) -> int:
    """Return the pixel width of a given column."""
    try:
        return _WIDTHS[column]
    except KeyError:
        return 35


_BORDER_LEFT_COLUMNS = [
    _US_NON_US,
    INSTITUTION_LABEL,
    _SOURCE_OF_FUNDS_US_ONLY,
    _NSF_MO_CORE,
    _GRAND_TOTAL,
]


def has_border_left(column: str) -> bool:
    """Return whether column has a border to its right."""
    return column in _BORDER_LEFT_COLUMNS
