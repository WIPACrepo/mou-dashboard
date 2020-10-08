"""REST interface for reading and writing MoU data."""


import logging
from typing import Any, cast, Dict, List, Optional, Tuple, TypedDict

import requests

# local imports
from rest_tools.client import RestClient  # type: ignore

from ..config import CONFIG
from .types import Record, Table

ID = "_id"


def _ds_rest_connection() -> RestClient:
    """Return REST Client connection object."""
    token_json = requests.get(CONFIG["TOKEN_REQUEST_URL"]).json()
    rc = RestClient(
        CONFIG["REST_SERVER_URL"], token=token_json["access"], timeout=5, retries=0
    )

    return rc


def _request(method: str, url: str, body: Any = None) -> Dict[str, Any]:
    logging.info(f"REQUEST :: {method} @ {url}, body: {body}")

    response = _ds_rest_connection().request_seq(method, url, body)

    def log_it(key: str, val: Any) -> Any:
        if key == "table":
            return f"{len(val)} records"
        if isinstance(val, dict):
            return val.keys()
        return val

    logging.info(f"RESPONSE ({method} @ {url}, body: {body}) ::")
    for key, val in response.items():
        logging.info(f"> {key}")
        logging.debug(f"-> {str(type(val).__name__)}")
        logging.debug(f"-> {log_it(key, val)}")
    return cast(Dict[str, Any], response)


# --------------------------------------------------------------------------------------
# Data/Table functions


def pull_data_table(
    institution: str = "",
    labor: str = "",
    with_totals: bool = False,
    snapshot: str = "",
    restore_id: str = "",
) -> Table:
    """Get table, optionally filtered by institution and/or labor.

    Grab a snapshot table, if snapshot is given. "" gives live table.
    """
    body = {
        "institution": institution,
        "labor": labor,
        "total_rows": with_totals,
        "snapshot": snapshot,
        "restore_id": restore_id,
    }
    response = _request("GET", "/table/data", body)

    return cast(Table, response["table"])


def push_record(
    record: Record, labor: str = "", institution: str = ""
) -> Optional[Record]:
    """Push new/changed record to source."""
    try:
        body = {"record": record, "institution": institution, "labor": labor}
        response = _request("POST", "/record", body)
        return cast(Record, response["record"])
    except requests.exceptions.HTTPError as e:
        logging.exception(f"EXCEPTED: {e}")
        return None


def delete_record(record: Record) -> bool:
    """Delete the record, return True if successful."""
    try:
        body = {"record": record}
        _request("DELETE", "/record", body)
        return True
    except requests.exceptions.HTTPError as e:
        logging.exception(f"EXCEPTED: {e}")
        return False


def list_snapshot_timestamps() -> List[str]:
    """Get the list of snapshots."""
    response = _request("GET", "/snapshots/timestamps")

    return cast(List[str], sorted(response["timestamps"], reverse=True))


def create_snapshot() -> str:
    """Create a snapshot."""
    response = _request("POST", "/snapshots/make")

    return cast(str, response["timestamp"])


def override_table(base64_file: str, filename: str) -> Tuple[str, int, str, str]:
    """Ingest .xlsx file as the new live collection.

    Return "" if successful, otherwise an error message.
    """
    try:
        body = {"base64_file": base64_file, "filename": filename}
        response = _request("POST", "/table/data", body)
        return (
            "",
            response["n_records"],
            response["previous_snapshot"],
            response["current_snapshot"],
        )
    except requests.exceptions.HTTPError as e:
        logging.exception(f"EXCEPTED: {e}")
        return str(e), 0, "", ""


# --------------------------------------------------------------------------------------
# Column functions


class TableConfigParser:
    """Manage caching and parsing responses from '/table/config'."""

    class Cache(TypedDict):
        """The response dict from '/table/config'."""

        columns: List[str]
        simple_dropdown_menus: Dict[str, List[str]]
        institutions: List[Tuple[str, str]]
        labor_categories: List[str]
        conditional_dropdown_menus: Dict[str, Tuple[str, Dict[str, List[str]]]]
        dropdowns: List[str]
        numerics: List[str]
        non_editables: List[str]
        hiddens: List[str]
        widths: Dict[str, int]
        border_left_columns: List[str]
        page_size: int

    def __init__(self, cached_table_config: Optional[Cache] = None) -> None:
        """Return the dictionary of table configurations.

        Use the parser functions to access configurations.
        """
        if cached_table_config:
            self.config = cached_table_config
        else:
            response = _request("GET", "/table/config")
            self.config = cast(TableConfigParser.Cache, response)

    def get_table_columns(self) -> List[str]:
        """Return table column's names."""
        return self.config["columns"]

    def get_simple_column_dropdown_menu(self, column: str) -> List[str]:
        """Return dropdown menu for a column."""
        return sorted(self.config["simple_dropdown_menus"][column])

    def get_institutions_w_abbrevs(self) -> List[Tuple[str, str]]:
        """Return list of institutions and their abbreviations."""
        return sorted(self.config["institutions"], key=lambda k: k[1])

    def get_labor_categories(self) -> List[str]:
        """Return list of labors."""
        return sorted(self.config["labor_categories"])

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

    def get_conditional_column_parent(self, column: str) -> Tuple[str, List[str]]:
        """Get the parent column's (name, list of options)."""
        return (
            self.config["conditional_dropdown_menus"][column][0],
            list(self.config["conditional_dropdown_menus"][column][1].keys()),
        )

    def get_conditional_column_dropdown_menu(
        self, column: str, parent_col_option: str
    ) -> List[str]:
        """Get the dropdown menu for a conditional dropdown-column."""
        return self.config["conditional_dropdown_menus"][column][1][parent_col_option]

    def get_column_width(self, column: str, default: int = 35) -> int:
        """Return the pixel width of a given column."""
        try:
            return self.config["widths"][column]
        except KeyError:
            return default

    def has_border_left(self, column: str) -> bool:
        """Return whether column has a border to its right."""
        return column in self.config["border_left_columns"]

    def get_page_size(self) -> int:
        """Return the number of rows for a page."""
        return self.config["page_size"]
