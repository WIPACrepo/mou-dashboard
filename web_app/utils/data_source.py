"""REST interface for reading and writing MoU data."""


from typing import Any, cast, Dict, List, Tuple

import pandas as pd  # type: ignore[import]

# read data from excel file
_DF = pd.read_excel("WBS.xlsx").fillna("")


# --------------------------------------------------------------------------------------
# Data/Table functions


def pull_data_table(institution: str = "", labor: str = "") -> List[Dict[str, Any]]:
    """Get table, optionally filtered by institution and/or labor."""
    dff = _DF
    # filter by labor
    if labor:
        dff = dff[dff["Labor Cat."] == labor]

    # filter by institution
    if institution:
        dff = dff[dff["Institution"] == institution]

    def _row(row: Dict[str, Any]) -> Dict[str, str]:
        for key in row.keys():
            if isinstance(row[key], float):
                row[key] = float(f"{row[key]:.2g}")
        return row

    # cast and remove any rows without any values
    table = [_row(r) for r in dff.to_dict("records") if any(r.values())]
    return table


def push_data_row(new_data_row: Dict[str, str]) -> None:
    """Push new/changed data row to source."""
    _DF.iloc[0] = new_data_row  # add as top row


# --------------------------------------------------------------------------------------
# Labor & Institution functions


_INSTITUTIONS = [i for i in _DF["Institution"].unique().tolist() if i]


def get_institutions() -> List[str]:
    """Return list of institutions."""
    return _INSTITUTIONS


_LABOR = [b for b in _DF["Labor Cat."].unique().tolist() if b]


def get_labor() -> List[str]:
    """Return list of labors."""
    return _LABOR


# --------------------------------------------------------------------------------------
# Column functions


def get_table_columns() -> List[str]:
    """Return table column's names."""
    return cast(List[str], _DF.columns)


_DROPDOWNS = ["WBS L2", "WBS L3", "Source of Funds (U.S. Only)"]

_SIMPLE_DROPDOWN_MENUS = {
    "WBS L2": [
        "2.1 Program Coordination",
        "2.2 Detector Operations & Maintenance (Online)",
        "2.3 Computing & Data Management Services",
        "2.4 Data Processing & Simulation Services",
        "2.5 Software",
        "2.6 Calibration",
    ],
    "Source of Funds (U.S. Only)": [
        "NSF M&O Core",
        "Base Grants",
        "US In-Kind",
        "Non-US In-kind",
    ],
}

_CONDITIONAL_DROPDOWN_MENUS = {
    "WBS L3": (
        "WBS L2",
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
    )
}


def get_simple_column_dropdown_menu(column: str) -> List[str]:
    """Return dropdown menu for a column."""
    return _SIMPLE_DROPDOWN_MENUS[column]


def is_column_dropdown(column: str) -> bool:
    """Return dropdown menu for a column."""
    return column in _DROPDOWNS


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
    return _CONDITIONAL_DROPDOWN_MENUS[column][1][dependee_column_option]
