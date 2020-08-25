"""REST interface for reading and writing MoU data."""


from typing import cast, Dict, List

import pandas as pd  # type: ignore[import]

# read data from excel file
_DF = pd.read_excel("WBS.xlsx").fillna("")


def get_table(institution: str = "", labor: str = "") -> List[Dict[str, str]]:
    """Get table, optionally filtered by institution and/or labor."""
    dff = _DF
    # filter by labor
    if labor:
        dff = dff[dff["Labor Cat."] == labor]

    # filter by institution
    if institution:
        dff = dff[dff["Institution"] == institution]

    return cast(List[Dict[str, str]], dff.to_dict("records"))


def get_table_columns() -> List[str]:
    """Return table column's names."""
    return cast(List[str], _DF.columns)


# Institutions and Labor Categories filter dropdown menus
_INSTITUTIONS = [i for i in _DF["Institution"].unique().tolist() if i]
print(f"INSTITUTIONS: {_INSTITUTIONS}")


def get_institutions() -> List[str]:
    """Return list of institutions."""
    return _INSTITUTIONS


_LABOR = [b for b in _DF["Labor Cat."].unique().tolist() if b]
print(f"LABOR: {_LABOR}")


def get_labor() -> List[str]:
    """Return list of labors."""
    return _LABOR


_PER_ROW_DROPDOWN = {
    "WBS L2": [
        "2.1 Program Coordination",
        "2.2 Detector Operations & Maintenance (Online)",
        "2.3 Computing & Data Management Services",
        "2.4 Data Processing & Simulation Services",
        "2.5 Software",
        "2.6 Calibration",
    ],
    "WBS L3": [
        "2.1.1 Administration",
        "2.2.1 Run Coordination",
        "2.3.1 Data Storage & Transfer",
        "2.4.1 Offline Data Production",
        "2.5.1 Core Software",
        "2.6.1 Detector Calibration",
    ],
    "Source of Funds (U.S. Only)": [
        "NSF M&O Core",
        "Base Grants",
        "US In-Kind",
        "Non-US In-kind",
    ],
}


def get_column_dropdown_menu(column: str) -> List[str]:
    """Return dropdown menu for a column."""
    return _PER_ROW_DROPDOWN[column]
