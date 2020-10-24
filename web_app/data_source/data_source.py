"""REST interface for reading and writing MoU data."""


from typing import Any, cast, Dict, Final, List, Optional, Tuple, TypedDict

from flask_login import current_user  # type: ignore[import]

from ..utils.types import InstitutionValues, Record, SnapshotInfo, Table
from . import table_config as tc
from .utils import mou_request

# constants
ID: Final[str] = "_id"
_OC_SUFFIX: Final[str] = "_original"


# --------------------------------------------------------------------------------------
# Data/Table-Conversion Functions


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


def _is_valid_simple_dropdown(
    parser: tc.TableConfigParser, record: Record, field: str
) -> bool:
    if not parser.is_simple_dropdown(field):
        raise Exception(f"not simple dropdown: {field} ({record})")

    if record[field] not in parser.get_simple_column_dropdown_menu(field):
        return False

    return True


def _is_valid_conditional_dropdown(
    parser: tc.TableConfigParser, record: Record, field: str
) -> bool:
    if not parser.is_conditional_dropdown(field):
        raise Exception(f"not conditional dropdown: {field} ({record})")

    try:
        parent_value = cast(str, record[parser.get_conditional_column_parent(field)])

        if record[field] not in parser.get_conditional_column_dropdown_menu(
            field, parent_value
        ):
            return False
    except KeyError:
        pass

    return True


def _remove_invalid_data(
    record: Record, tconfig_cache: tc.TableConfigParser.Cache
) -> Record:
    """Remove items whose data aren't valid."""

    def _remove_orphans(_record: Record) -> Record:
        """Remove orphaned child fields."""
        return {
            k: v
            for k, v in record.items()
            if not tconfig.is_conditional_dropdown(k)
            or tconfig.get_conditional_column_parent(k) in record
        }

    tconfig = tc.TableConfigParser(tconfig_cache)

    # remove blank fields
    record = {k: v for k, v in record.items() if v not in [None, ""]}
    record = _remove_orphans(record)

    # check that simple-dropdown selections are valid
    record = {
        k: v
        for k, v in record.items()
        if not tconfig.is_simple_dropdown(k)
        or _is_valid_simple_dropdown(tconfig, record, k)
    }
    record = _remove_orphans(record)

    # check that conditional-dropdown selections are valid
    record = {
        k: v
        for k, v in record.items()
        if not tconfig.is_conditional_dropdown(k)
        or _is_valid_conditional_dropdown(tconfig, record, k)
    }
    record = _remove_orphans(record)

    # add (back) missing fields as blanks
    record.update({k: "" for k in tconfig.get_table_columns() if k not in record})

    return record


def _convert_record_dash_to_rest(
    record: Record, tconfig_cache: Optional[tc.TableConfigParser.Cache] = None
) -> Record:
    """Convert a record from Dash's datatable to be sent to the rest server.

    Copy but leave out the touchstone columns used to detect changed
    values.
    """
    out_record = {k: v for k, v in record.items() if not _is_touchstone_column(k)}

    if tconfig_cache:
        out_record = _remove_invalid_data(out_record, tconfig_cache)

    return out_record


# --------------------------------------------------------------------------------------
# Data/Table Functions


def pull_data_table(
    wbs_l1: str,
    institution: str = "",
    labor: str = "",
    with_totals: bool = False,
    snapshot_ts: str = "",
    restore_id: str = "",
) -> Table:
    """Get table, optionally filtered by institution and/or labor.

    Grab a snapshot table, if snapshot is given. "" gives live table.
    # TODO - it would be nice to split out restore_id into its own thing

    Keyword Arguments:
        institution {str} -- filter by institution (default: {""})
        labor {str} -- filter by labor category (default: {""})
        with_totals {bool} -- whether to include "total" rows (default: {False})
        snapshot {str} -- name of snapshot (default: {""})
        restore_id {str} -- id of a record to be restored (default: {""})

    Returns:
        Table -- the returned table
    """
    assert wbs_l1 and isinstance(wbs_l1, str)
    assert isinstance(institution, str)
    assert isinstance(labor, str)
    assert isinstance(with_totals, bool)
    assert isinstance(snapshot_ts, str)
    assert isinstance(restore_id, str)

    class _RespTableData(TypedDict):
        table: Table

    # request
    body = {
        "institution": institution,
        "labor": labor,
        "total_rows": with_totals,
        "snapshot": snapshot_ts,
        "restore_id": restore_id,
    }

    response = cast(
        _RespTableData, mou_request("GET", f"/table/data/{wbs_l1}", body=body),
    )
    # get & convert
    return _convert_table_rest_to_dash(response["table"])


def push_record(  # pylint: disable=R0913
    wbs_l1: str,
    record: Record,
    labor: str = "",
    institution: str = "",
    novel: bool = False,
    tconfig_cache: Optional[tc.TableConfigParser.Cache] = None,
) -> Record:
    """Push new/changed record to source.

    Arguments:
        record {Record} -- the record

    Keyword Arguments:
        tconfig_cache {Optional[tc.TableConfigParser.Cache]} -- pass to remove invalid record data (default: {None})
        labor {str} -- labor category value to be inserted into record (default: {""})
        institution {str} -- institution value to be inserted into record (default: {""})
        novel {bool} -- whether the record is new (default: {False})

    Returns:
        Record -- the returned record
    """
    assert wbs_l1 and isinstance(wbs_l1, str)
    assert isinstance(record, dict)
    assert isinstance(labor, str)
    assert isinstance(institution, str)
    assert isinstance(novel, bool)
    assert isinstance(tconfig_cache, (dict, type(None)))

    class _RespRecord(TypedDict):
        record: Record

    # request
    body = {
        "record": _convert_record_dash_to_rest(record, tconfig_cache),
        "institution": institution,
        "labor": labor,
    }
    response = cast(_RespRecord, mou_request("POST", f"/record/{wbs_l1}", body=body))
    # get & convert
    return _convert_record_rest_to_dash(response["record"], novel=novel)


def delete_record(wbs_l1: str, record_id: str) -> None:
    """Delete the record, return True if successful."""
    assert wbs_l1 and isinstance(wbs_l1, str)
    assert isinstance(record_id, str)

    body = {"record_id": record_id}
    mou_request("DELETE", f"/record/{wbs_l1}", body=body)


def list_snapshots(wbs_l1: str) -> List[SnapshotInfo]:
    """Get the list of snapshots."""
    assert wbs_l1 and isinstance(wbs_l1, str)

    class _RespSnapshots(TypedDict):
        snapshots: List[SnapshotInfo]

    response = cast(_RespSnapshots, mou_request("GET", f"/snapshots/list/{wbs_l1}"),)
    return sorted(response["snapshots"], key=lambda i: i["timestamp"], reverse=True)


def create_snapshot(wbs_l1: str, name: str) -> SnapshotInfo:
    """Create a snapshot."""
    assert wbs_l1 and isinstance(wbs_l1, str)
    assert isinstance(name, str)

    body = {"creator": current_user.name, "name": name}
    response = mou_request("POST", f"/snapshots/make/{wbs_l1}", body=body)
    return cast(SnapshotInfo, response)


def override_table(
    wbs_l1: str, base64_file: str, filename: str
) -> Tuple[int, Optional[SnapshotInfo], Optional[SnapshotInfo]]:
    """Ingest .xlsx file as the new live collection.

    Arguments:
        base64_file {str} -- xlsx file contents base64-encoded
        filename {str} -- the name of the file

    Returns:
        int -- number of records added in the table
        str -- snapshot name of the previous live table ('' if no prior table)
        str -- snapshot name of the current live table
    """
    assert wbs_l1 and isinstance(wbs_l1, str)
    assert isinstance(base64_file, str)
    assert isinstance(filename, str)

    class _RespTableData(TypedDict):
        n_records: int
        previous_snapshot: SnapshotInfo
        current_snapshot: SnapshotInfo

    body = {
        "base64_file": base64_file,
        "filename": filename,
        "creator": current_user.name,
    }
    response = cast(
        _RespTableData, mou_request("POST", f"/table/data/{wbs_l1}", body=body),
    )
    return (
        response["n_records"],
        response["previous_snapshot"],
        response["current_snapshot"],
    )


def pull_institution_values(
    wbs_l1: str, snapshot_timestamp: str, institution: str
) -> InstitutionValues:
    """Get the institution's values."""
    assert wbs_l1 and isinstance(wbs_l1, str)
    assert isinstance(snapshot_timestamp, str)
    assert isinstance(institution, str)

    body = {"institution": institution, "snapshot_timestamp": snapshot_timestamp}
    response = mou_request("GET", f"/institution/values/{wbs_l1}", body=body)
    return cast(InstitutionValues, response)


def push_institution_values(
    wbs_l1: str, institution: str, values: InstitutionValues
) -> None:
    """Push the institution's values."""
    assert wbs_l1 and isinstance(wbs_l1, str)
    assert isinstance(institution, str)
    assert isinstance(values, dict)

    body = {"institution": institution}
    body.update(cast(Dict[str, Any], values))
    _ = mou_request("POST", f"/institution/values/{wbs_l1}", body=body)
