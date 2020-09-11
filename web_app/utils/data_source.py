"""REST interface for reading and writing MoU data."""


from copy import deepcopy
from typing import cast, Dict, List, Optional, Tuple, TypedDict
from urllib.parse import urljoin

import pandas as pd  # type: ignore[import]
import requests

# local imports
from keycloak_setup.icecube_setup import ICECUBE_INSTS  # type: ignore[import]
from rest_tools.client import RestClient  # type: ignore

from ..config import AUTH_PREFIX, REST_SERVER_URL, TOKEN_SERVER_URL
from .types import Record, Table


def ds_rest_connection() -> RestClient:
    """Return REST Client connection object."""
    token_request_url = urljoin(TOKEN_SERVER_URL, f"token?scope={AUTH_PREFIX}:web")
    token_json = requests.get(token_request_url).json()

    rc = RestClient(REST_SERVER_URL, token=token_json["access"], timeout=5, retries=0)
    return rc


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


# --------------------------------------------------------------------------------------
# Data/Table functions


def pull_data_table(institution: str = "", labor: str = "") -> Table:
    """Get table, optionally filtered by institution and/or labor."""
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

    return cast(Table, table)


def _next_id() -> str:
    return f"{max(_TABLE.keys())}{max(_TABLE.keys())}"


def push_record(
    record: Record, labor: str = "", institution: str = ""
) -> Optional[Record]:
    """Push new/changed record to source."""
    record[_INSTITUTION] = institution
    record[_LABOR_CAT] = labor

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


class TableConfig:
    """Manage caching and parsing responses from '/table/config'."""

    class _ResponseTypedDict(TypedDict):
        """The response dict from '/table/config'."""

        columns: List[str]
        simple_dropdown_menus: Dict[str, List[str]]
        conditional_dropdown_menus: Dict[str, Tuple[str, Dict[str, List[str]]]]
        dropdowns: List[str]
        numerics: List[str]
        non_editables: List[str]
        hiddens: List[str]
        widths: Dict[str, int]
        border_left_columns: List[str]
        page_size: int

    def __init__(self) -> None:
        """Return the dictionary of table configurations.

        Use the parser functions to access configurations.
        """
        rc = ds_rest_connection()
        response = rc.request_seq("GET", "/table/config")
        self.config = cast(TableConfig._ResponseTypedDict, response)

    def get_table_columns(self) -> List[str]:
        """Return table column's names."""
        return self.config["columns"]

    def get_simple_column_dropdown_menu(self, column: str) -> List[str]:
        """Return dropdown menu for a column."""
        return self.config["simple_dropdown_menus"][column]

    def get_institutions(self) -> List[str]:
        """Return list of institutions."""
        return self.get_simple_column_dropdown_menu(_INSTITUTION)

    def get_labor_categories(self) -> List[str]:
        """Return list of labors."""
        return self.get_simple_column_dropdown_menu(_LABOR_CAT)

    def is_column_dropdown(self, column: str) -> bool:
        """Return  whether column is a dropdown-type."""
        return column in self.config["dropdowns"]

    def is_column_numeric(self, column: str) -> bool:
        """Return whether column takes numeric data."""
        return column in self.config["numerics"]

    def is_column_editable(self, column: str) -> bool:
        """Return whether column data can be edited by end-user."""
        return column not in self.config["non_editables"]

    def get_hidden_columns(self) -> List[str]:
        """Return the columns hidden be default."""
        return self.config["hiddens"]

    def get_dropdown_columns(self) -> List[str]:
        """Return list of dropdown-type columns."""
        return self.config["dropdowns"]

    def is_simple_dropdown(self, column: str) -> bool:
        """Return whether column is a simple dropdown-type."""
        return column in self.config["simple_dropdown_menus"].keys()

    def is_conditional_dropdown(self, column: str) -> bool:
        """Return whether column is a conditional dropdown-type."""
        return column in self.config["conditional_dropdown_menus"].keys()

    def get_conditional_column_dependee(self, column: str) -> Tuple[str, List[str]]:
        """Get the dependee column's (name and list of options)."""
        return (
            self.config["conditional_dropdown_menus"][column][0],
            list(self.config["conditional_dropdown_menus"][column][1].keys()),
        )

    def get_conditional_column_dropdown_menu(
        self, column: str, dependee_column_option: str
    ) -> List[str]:
        """Get the dropdown menu for a conditional dropdown-column."""
        return self.config["conditional_dropdown_menus"][column][1][
            dependee_column_option
        ]

    def get_column_width(self, column: str) -> int:
        """Return the pixel width of a given column."""
        try:
            return self.config["widths"][column]
        except KeyError:
            return 35

    def has_border_left(self, column: str) -> bool:
        """Return whether column has a border to its right."""
        return column in self.config["border_left_columns"]

    def get_page_size(self) -> int:
        """Return the number of rows for a page."""
        return self.config["page_size"]
