"""REST interface for reading and writing MoU data."""


import logging
from typing import Any, cast, Dict, Final, List, Optional, Tuple, TypedDict

import requests

# local imports
from rest_tools.client import RestClient  # type: ignore

from ..config import CONFIG
from ..utils.types import Record, Table

# constants
ID: Final[str] = "_id"
_OC_SUFFIX: Final[str] = "_original"


def _rest_connection() -> RestClient:
    """Return REST Client connection object."""
    if CONFIG["TOKEN"]:
        token = CONFIG["TOKEN"]
    else:
        token_json = requests.get(CONFIG["TOKEN_REQUEST_URL"]).json()
        token = token_json["access"]

    rc = RestClient(CONFIG["REST_SERVER_URL"], token=token, timeout=5, retries=0)

    return rc


def _request(method: str, url: str, body: Any = None) -> Dict[str, Any]:
    logging.info(f"REQUEST :: {method} @ {url}, body: {body}")

    response: Dict[str, Any] = _rest_connection().request_seq(method, url, body)

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

    return response


# --------------------------------------------------------------------------------------
# Record/Table Conversion Functions


def get_touchstone_name(column: str) -> str:
    """Return the column name for detecting changed data.

    For use as an "if" value in a DataTable.style_data_conditional
    entry's filter query.
    """
    return f"{column}{_OC_SUFFIX}"


def _is_touchstone_column(column: str) -> bool:
    return column.endswith(_OC_SUFFIX)


def _convert_record_rest_to_dash(record: Record, novel: bool = False) -> Record:
    """Convert a record to be added to Dash's datatable.

    Make a copy of each field in an new column to detect changed values.
    These columns aren't meant to be seen by the user.

    Arguments:
        record {Record} -- the record, that will be updated

    Keyword Arguments:
        novel {bool} -- if True, don't copy values, just set as '' (default: {False})

    Returns:
        Record -- the argument value
    """
    for field in record:  # don't add copies of copies, AKA make it safe to call this 2x
        if _is_touchstone_column(field):
            return record

    # add touchstone columns (if not `novel`)
    if not novel:
        record.update({get_touchstone_name(k): v for k, v in record.items()})
    else:
        record.update({get_touchstone_name(k): "" for k, _ in record.items()})

    return record


def _convert_table_rest_to_dash(table: Table) -> Table:
    """Convert a table to be added as Dash's datatable.

    Make a copy of each column to detect changed values (aka the
    touchstone column). Hide these touchstone columns by not adding them
    to the Dash's datatable's `columns` property.
    """
    for record in table:
        _convert_record_rest_to_dash(record)

    return table


def _convert_record_dash_to_rest(record: Record) -> Record:
    """Convert a record from Dash's datatable to be sent to the rest server.

    Copy but leave out the touchstone columns used to detect changed
    values.
    """
    ds_record = {k: v for k, v in record.items() if not _is_touchstone_column(k)}

    # if ds_record.get()

    return ds_record


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

    class RespTableData(TypedDict):  # pylint: disable=C0115,R0903
        table: Table

    # request
    body = {
        "institution": institution,
        "labor": labor,
        "total_rows": with_totals,
        "snapshot": snapshot,
        "restore_id": restore_id,
    }
    response = cast(RespTableData, _request("GET", "/table/data", body))
    # get & convert
    return _convert_table_rest_to_dash(response["table"])


def push_record(
    record: Record, labor: str = "", institution: str = "", novel: bool = False
) -> Optional[Record]:
    """Push new/changed record to source."""

    class RespRecord(TypedDict):  # pylint: disable=C0115,R0903
        record: Record

    try:
        # request
        body = {
            "record": _convert_record_dash_to_rest(record),
            "institution": institution,
            "labor": labor,
        }
        response = cast(RespRecord, _request("POST", "/record", body))
        # get & convert
        return _convert_record_rest_to_dash(response["record"], novel=novel)
    except requests.exceptions.HTTPError as e:
        logging.exception(f"EXCEPTED: {e}")
        return None


def delete_record(record_id: str) -> bool:
    """Delete the record, return True if successful."""
    try:
        body = {"record_id": record_id}
        _request("DELETE", "/record", body)
        return True
    except requests.exceptions.HTTPError as e:
        logging.exception(f"EXCEPTED: {e}")
        return False


def list_snapshot_timestamps() -> List[str]:
    """Get the list of snapshots."""

    class RespSnapshotsTimestamps(TypedDict):  # pylint: disable=C0115,R0903
        timestamps: List[str]

    response = cast(RespSnapshotsTimestamps, _request("GET", "/snapshots/timestamps"))

    return sorted(response["timestamps"], reverse=True)


def create_snapshot() -> str:
    """Create a snapshot."""

    class RespSnapshotsMake(TypedDict):  # pylint: disable=C0115,R0903
        timestamp: str

    response = cast(RespSnapshotsMake, _request("POST", "/snapshots/make"))

    return response["timestamp"]


def override_table(base64_file: str, filename: str) -> Tuple[str, int, str, str]:
    """Ingest .xlsx file as the new live collection.

    Arguments:
        base64_file {str} -- xlsx file contents base64-encoded
        filename {str} -- the name of the file

    Returns:
        str -- error message ('' if successful)
        int -- number of records added in the table
        str -- snapshot name of the previous live table ('' if no prior table)
        str -- snapshot name of the current live table
    """

    class RespTableData(TypedDict):  # pylint: disable=C0115,R0903
        n_records: int
        previous_snapshot: str
        current_snapshot: str

    try:
        body = {"base64_file": base64_file, "filename": filename}
        response = cast(RespTableData, _request("POST", "/table/data", body))
        return (
            "",
            response["n_records"],
            response["previous_snapshot"],
            response["current_snapshot"],
        )
    except requests.exceptions.HTTPError as e:
        logging.exception(f"EXCEPTED: {e}")
        return str(e), 0, "", ""
