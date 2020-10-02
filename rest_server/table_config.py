"""Values for the table config."""


from typing import Any, Dict, Final, List, Tuple, TypedDict, Union

# local imports
from keycloak_setup.icecube_setup import ICECUBE_INSTS  # type: ignore[import]

ID = "_id"
WBS_L2 = "WBS L2"
WBS_L3 = "WBS L3"
LABOR_CAT = "Labor Cat."
US_NON_US = "US / Non-US"
INSTITUTION = "Institution"
_NAMES = "Names"
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


class _ColumnConfigTypedDict(TypedDict, total=False):
    """TypedDict for column configs."""

    width: int
    non_editable: bool
    hidden: bool
    options: List[str]
    sort_order: int
    conditional_parent: str
    conditional_options: Dict[str, List[str]]
    border_left: bool
    on_the_fly: bool
    funding_source: bool
    numeric: bool


_COLUMN_CONFIGS: Final[Dict[str, _ColumnConfigTypedDict]] = {
    ID: {"width": 100, "non_editable": True, "hidden": True},
    WBS_L2: {
        "width": 350,
        "options": [
            "2.1 Program Coordination",
            "2.2 Detector Operations & Maintenance (Online)",
            "2.3 Computing & Data Management Services",
            "2.4 Data Processing & Simulation Services",
            "2.5 Software",
            "2.6 Calibration",
        ],
        "sort_order": 1,
    },
    WBS_L3: {
        "width": 300,
        "conditional_parent": "WBS_L2",
        "conditional_options": {
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
        "sort_order": 2,
    },
    US_NON_US: {
        "width": 100,
        "non_editable": True,
        "hidden": True,
        "border_left": True,
        "on_the_fly": True,
        "sort_order": 3,
    },
    INSTITUTION: {
        "width": 140,
        "options": sorted(set(inst["abbreviation"] for inst in ICECUBE_INSTS.values())),
        "border_left": True,
        "sort_order": 4,
    },
    LABOR_CAT: {
        "width": 125,
        "options": ["AD", "CS", "DS", "EN", "GR", "IT", "KE", "MA", "PO", "SC", "WO"],
        "sort_order": 5,
    },
    _NAMES: {"width": 150, "sort_order": 6},
    _TASKS: {"width": 300},
    SOURCE_OF_FUNDS_US_ONLY: {
        "width": 185,
        "conditional_parent": US_NON_US,
        "conditional_options": {
            US: [NSF_MO_CORE, NSF_BASE_GRANTS, US_IN_KIND],
            NON_US: [NON_US_IN_KIND],
        },
        "border_left": True,
        "sort_order": 7,
    },
    FTE: {"width": 90, "numeric": True},
    TOTAL_COL: {
        "width": 400,
        "non_editable": True,
        "hidden": True,
        "border_left": True,
        "on_the_fly": True,
    },
    NSF_MO_CORE: {
        "width": 110,
        "funding_source": True,
        "non_editable": True,
        "hidden": True,
        "numeric": True,
        "on_the_fly": True,
    },
    NSF_BASE_GRANTS: {
        "width": 110,
        "funding_source": True,
        "non_editable": True,
        "hidden": True,
        "numeric": True,
        "on_the_fly": True,
    },
    US_IN_KIND: {
        "width": 110,
        "funding_source": True,
        "non_editable": True,
        "hidden": True,
        "numeric": True,
        "on_the_fly": True,
    },
    NON_US_IN_KIND: {
        "width": 110,
        "funding_source": True,
        "non_editable": True,
        "hidden": True,
        "numeric": True,
        "on_the_fly": True,
    },
    GRAND_TOTAL: {
        "width": 110,
        "numeric": True,
        "non_editable": True,
        "hidden": True,
        "border_left": True,
        "on_the_fly": True,
    },
}


def get_columns() -> List[str]:
    """Get the columns."""
    return list(_COLUMN_CONFIGS.keys())


def get_institutions_and_abbrevs() -> List[Tuple[str, str]]:
    """Get the institutions and their abbreviations."""
    abbrevs: Dict[str, str] = {}
    for inst, val in ICECUBE_INSTS.items():
        # for institutions with the same abbreviation (aka different departments)
        # append their name
        if val["abbreviation"] in abbrevs:
            abbrevs[val["abbreviation"]] = f"{abbrevs[val['abbreviation']]} / {inst}"
        else:
            abbrevs[val["abbreviation"]] = inst

    return [(name, abbrev) for abbrev, name in abbrevs.items()]


def get_labor_cats() -> List[str]:
    """Get the labor categories."""
    return _COLUMN_CONFIGS[LABOR_CAT]["options"]


def get_l2_categories() -> List[str]:
    """Get the L2 categories."""
    return _COLUMN_CONFIGS[WBS_L2]["options"]


def get_l3_categories_by_l2(l2: str) -> List[str]:  # pylint: disable=C0103
    """Get the L3 categories for an L2 value."""
    return _COLUMN_CONFIGS[WBS_L3]["conditional_options"][l2]


def get_simple_dropdown_menus() -> Dict[str, List[str]]:
    """Get the columns that are simple dropdowns."""
    return {
        col: config["options"]
        for col, config in _COLUMN_CONFIGS.items()
        if "options" in config
    }


def get_conditional_dropdown_menus() -> Dict[str, Tuple[str, Dict[str, List[str]]]]:
    """Get the columns (and conditions) that are conditionally dropdowns."""
    return {
        col: (config["conditional_parent"], config["conditional_options"])
        for col, config in _COLUMN_CONFIGS.items()
        if ("conditional_parent" in config) and ("conditional_options" in config)
    }


def get_dropdowns() -> List[str]:
    """Get the columns that are dropdowns."""
    return list(get_simple_dropdown_menus().keys()) + list(
        get_conditional_dropdown_menus().keys()
    )


def get_numerics() -> List[str]:
    """Get the columns that have numeric data."""
    return [col for col, config in _COLUMN_CONFIGS.items() if config.get("numeric")]


def get_non_editables() -> List[str]:
    """Get the columns that are not editable."""
    return [
        col for col, config in _COLUMN_CONFIGS.items() if config.get("non_editable")
    ]


def get_hiddens() -> List[str]:
    """Get the columns that are hidden."""
    return [col for col, config in _COLUMN_CONFIGS.items() if config.get("hidden")]


def get_widths() -> Dict[str, int]:
    """Get the widths of each column."""
    return {col: config["width"] for col, config in _COLUMN_CONFIGS.items()}


def get_border_left_columns() -> List[str]:
    """Get the columns that have a left border."""
    return [col for col, config in _COLUMN_CONFIGS.items() if config.get("border_left")]


def get_page_size() -> int:
    """Get page size."""
    return 17


def get_on_the_fly_fields() -> List[str]:
    """Get names of fields created on-the-fly, data not stored."""
    return [col for col, config in _COLUMN_CONFIGS.items() if config.get("on_the_fly")]


def sort_key(  # pylint: disable=C0103
    k: Dict[str, Union[int, float, str]]
) -> Tuple[Any, ...]:
    """Sort key for the table."""
    sort_keys: List[Union[int, float, str]] = []

    column_orders = {
        col: config["sort_order"]
        for col, config in _COLUMN_CONFIGS.items()
        if "sort_order" in config
    }
    columns_by_precedence = sorted(column_orders.keys(), key=lambda x: column_orders[x])

    for col in columns_by_precedence:
        sort_keys.append(k.get(col, "ZZZZ"))  # HACK: sort empty/missing values last

    return tuple(sort_keys)
