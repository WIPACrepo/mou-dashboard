"""REST interface for reading and writing MoU data."""


from typing import Any, cast, Dict, Final, List, Optional, Tuple, TypedDict, Union

from flask_login import current_user  # type: ignore[import]

from ..utils import types, utils
from . import table_config as tc
from .utils import mou_request

# constants
_OC_SUFFIX: Final[str] = "_original"


# --------------------------------------------------------------------------------------
# Data/types.Table-Conversion Functions


def get_touchstone_name(column: str) -> str:
    """Return the column name for detecting changed data.

    For use as an "if" value in a DataTable.style_data_conditional
    entry's filter query.
    """
    return f"{column}{_OC_SUFFIX}"


def _is_touchstone_column(column: str) -> bool:
    return column.endswith(_OC_SUFFIX)


def _convert_record_rest_to_dash(
    record: types.Record, tconfig: tc.TableConfigParser, novel: bool = False
) -> types.Record:
    """Convert a record to be added to Dash's datatable.

    Make a copy of each field in an new column to detect changed values.
    These columns aren't meant to be seen by the user.

    Arguments:
        record {types.Record} -- the record, that will be updated

    Keyword Arguments:
        novel {bool} -- if True, don't copy values, just set as '' (default: {False})

    Returns:
        types.Record -- the argument value
    """
    if ts := record.get(tconfig.const.TIMESTAMP):
        record[tconfig.const.TIMESTAMP] = utils.get_iso(str(ts))

    if not record.get(tconfig.const.EDITOR):
        record[tconfig.const.EDITOR] = "—"

    for field in record:  # don't add copies of copies, AKA make it safe to call this 2x
        if _is_touchstone_column(field):
            return record

    # add touchstone columns (if not `novel`)
    if not novel:
        record.update({get_touchstone_name(k): v for k, v in record.items()})
    else:
        record.update({get_touchstone_name(k): "" for k, _ in record.items()})

    return record


def _convert_table_rest_to_dash(
    table: types.Table, tconfig: tc.TableConfigParser
) -> types.Table:
    """Convert a table to be added as Dash's datatable.

    Make a copy of each column to detect changed values (aka the
    touchstone column). Hide these touchstone columns by not adding them
    to the Dash's datatable's `columns` property.
    """
    for record in table:
        _convert_record_rest_to_dash(record, tconfig)

    return table


def _is_valid_simple_dropdown(
    parser: tc.TableConfigParser, record: types.Record, field: str
) -> bool:
    if not parser.is_simple_dropdown(field):
        raise Exception(f"not simple dropdown: {field} ({record})")

    if record[field] not in parser.get_simple_column_dropdown_menu(field):
        return False

    return True


def _is_valid_conditional_dropdown(
    parser: tc.TableConfigParser, record: types.Record, field: str
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
    record: types.Record, tconfig: tc.TableConfigParser
) -> types.Record:
    """Remove items whose data aren't valid."""

    def _remove_orphans(_record: types.Record) -> types.Record:
        """Remove orphaned child fields."""
        return {
            k: v
            for k, v in record.items()
            if not tconfig.is_conditional_dropdown(k)
            or tconfig.get_conditional_column_parent(k) in record
        }

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
    record: types.Record, tconfig: Optional[tc.TableConfigParser] = None
) -> types.Record:
    """Convert a record from Dash's datatable to be sent to the rest server.

    Copy but leave out the touchstone columns used to detect changed
    values.
    """
    out_record = {k: v for k, v in record.items() if not _is_touchstone_column(k)}

    if tconfig:
        out_record = _remove_invalid_data(out_record, tconfig)

    return out_record


def record_to_strings(record: types.Record, tconfig: tc.TableConfigParser) -> List[str]:
    """Get a string representation of the record."""
    strings = []
    for field, value in _convert_record_dash_to_rest(record).items():
        if field == tconfig.const.ID:
            continue
        if not value and value != 0:
            continue
        strings.append(f"{field}: {value}")

    return strings


def _validate(
    data: Any,
    in_type: Union[type, Tuple[type, ...]],
    falsy_okay: bool = True,
    out: Optional[type] = None,
) -> Any:
    """Type-check `data`. Optionally, convert and return.

    Arguments:
        data {Any} -- data to be validated
        in_type {Union[type, Tuple[type, ...]]} -- allowed type(s)

    Keyword Arguments:
        falsy_okay {bool} -- otherwise, raise `TypeError` if `not data` (default: {True})
        out {Optional[type]} -- assure `data`'s returned type, AND assign `out`'s default falsy value (if `not data`) (default: {None})

    Returns:
        Any -- `data` potentially changed/converted

    Raises:
        TypeError -- raised if any type check failed
    """
    # check incoming type
    if not isinstance(data, in_type):
        raise TypeError(f"{data=} is {type(data)=}, should be {in_type=}")

    # check if data is falsy
    if (not data) and (not falsy_okay):
        raise TypeError(f"{data=} is falsy ({in_type=})")

    if out:
        # get the falsy/default type's value, Ex: data = str()
        if not data:
            data = out()
        # check outgoing type
        if not isinstance(data, out):
            raise TypeError(f"{data=} is {type(data)=}, should be {out=}")

    return data


# --------------------------------------------------------------------------------------
# Data/types.Table Functions


def pull_data_table(  # pylint: disable=R0913
    wbs_l1: str,
    tconfig: tc.TableConfigParser,
    institution: types.DashVal = "",
    labor: types.DashVal = "",
    with_totals: bool = False,
    snapshot_ts: types.DashVal = "",
    restore_id: str = "",
    raw: bool = False,
) -> types.Table:
    """Get table, optionally filtered by institution and/or labor.

    Grab a snapshot table, if `snapshot_ts` is given ("" gives live table).
    # TODO - it would be nice to split out restore_id into its own thing

    Keyword Arguments:
        institution {str} -- filter by institution (default: {""})
        labor {str} -- filter by labor category (default: {""})
        with_totals {bool} -- whether to include "total" rows (default: {False})
        snapshot_ts {str} -- name of snapshot (default: {""})
        restore_id {str} -- id of a record to be restored (default: {""})
        raw -- {bool} -- True if data isn't for datatable display (default: {False})

    Returns:
        types.Table -- the returned table
    """
    _validate(wbs_l1, str, falsy_okay=False)
    institution = _validate(institution, types.DashVal_types, out=str)
    labor = _validate(labor, types.DashVal_types, out=str)
    _validate(with_totals, bool)
    snapshot_ts = _validate(snapshot_ts, types.DashVal_types, out=str)
    _validate(restore_id, str)

    class _RespTableData(TypedDict):
        table: types.Table

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
    if raw:
        return response["table"]
    return _convert_table_rest_to_dash(response["table"], tconfig)


def push_record(  # pylint: disable=R0913
    wbs_l1: str,
    record: types.Record,
    tconfig: tc.TableConfigParser,
    task: str = "",
    labor: types.DashVal = "",
    institution: types.DashVal = "",
    novel: bool = False,
) -> types.Record:
    """Push new/changed record to source.

    Keyword Arguments:
        labor {str} -- labor category value to be inserted into record (default: {""})
        institution {str} -- institution value to be inserted into record (default: {""})
        novel {bool} -- whether the record is new (default: {False})

    Returns:
        types.Record -- the returned record
    """
    _validate(wbs_l1, str, falsy_okay=False)
    _validate(record, dict)
    _validate(task, str)
    labor = _validate(labor, types.DashVal_types, out=str)
    institution = _validate(institution, types.DashVal_types, out=str)
    _validate(novel, bool)
    _validate(tconfig, tc.TableConfigParser)

    class _RespRecord(TypedDict):
        record: types.Record

    # request
    body: Dict[str, Any] = {
        "record": _convert_record_dash_to_rest(record, tconfig),
        "editor": current_user.name,
    }
    if institution:
        body["institution"] = institution
    if labor:
        body["labor"] = labor
    if task:
        body["task"] = task.replace("\n", " ")
    response = cast(_RespRecord, mou_request("POST", f"/record/{wbs_l1}", body=body))
    # get & convert
    return _convert_record_rest_to_dash(response["record"], tconfig, novel=novel)


def delete_record(wbs_l1: str, record_id: str) -> None:
    """Delete the record, return True if successful."""
    _validate(wbs_l1, str, falsy_okay=False)
    _validate(record_id, str)

    body = {
        "record_id": record_id,
        "editor": current_user.name,
    }
    mou_request("DELETE", f"/record/{wbs_l1}", body=body)


def list_snapshots(wbs_l1: str) -> List[types.SnapshotInfo]:
    """Get the list of snapshots."""
    _validate(wbs_l1, str, falsy_okay=False)

    class _RespSnapshots(TypedDict):
        snapshots: List[types.SnapshotInfo]

    body = {
        "is_admin": current_user.is_authenticated and current_user.is_admin,
    }
    response = cast(
        _RespSnapshots, mou_request("GET", f"/snapshots/list/{wbs_l1}", body)
    )

    return sorted(response["snapshots"], key=lambda i: i["timestamp"], reverse=True)


def create_snapshot(wbs_l1: str, name: str) -> types.SnapshotInfo:
    """Create a snapshot."""
    _validate(wbs_l1, str, falsy_okay=False)
    _validate(name, str)

    body = {
        "creator": current_user.name,
        "name": name,
    }
    response = mou_request("POST", f"/snapshots/make/{wbs_l1}", body=body)
    return cast(types.SnapshotInfo, response)


def override_table(
    wbs_l1: str, base64_file: str, filename: str
) -> Tuple[int, Optional[types.SnapshotInfo], Optional[types.SnapshotInfo]]:
    """Ingest .xlsx file as the new live collection.

    Arguments:
        base64_file {str} -- xlsx file contents base64-encoded
        filename {str} -- the name of the file

    Returns:
        int -- number of records added in the table
        str -- snapshot name of the previous live table ('' if no prior table)
        str -- snapshot name of the current live table
    """
    _validate(wbs_l1, str, falsy_okay=False)
    _validate(base64_file, str)
    _validate(filename, str)

    class _RespTableData(TypedDict):
        n_records: int
        previous_snapshot: types.SnapshotInfo
        current_snapshot: types.SnapshotInfo

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
    wbs_l1: str, snapshot_ts: types.DashVal, institution: types.DashVal
) -> Tuple[
    Optional[int],
    Optional[int],
    Optional[int],
    Optional[int],
    Optional[int],
    Optional[int],
    str,
    bool,
    bool,
]:
    """Get the institution's values."""
    _validate(wbs_l1, str, falsy_okay=False)
    snapshot_ts = _validate(snapshot_ts, types.DashVal_types, out=str)
    institution = _validate(institution, types.DashVal_types, out=str)

    body = {
        "institution": institution,
        "snapshot_timestamp": snapshot_ts,
    }
    response = mou_request("GET", f"/institution/values/{wbs_l1}", body=body)
    return (
        cast(Optional[int], response.get("phds_authors")),
        cast(Optional[int], response.get("faculty")),
        cast(Optional[int], response.get("scientists_post_docs")),
        cast(Optional[int], response.get("grad_students")),
        cast(Optional[int], response.get("cpus")),
        cast(Optional[int], response.get("gpus")),
        cast(str, response.get("text", "")),
        cast(bool, response.get("headcounts_confirmed", False)),
        cast(bool, response.get("computing_confirmed", False)),
    )


def push_institution_values(  # pylint: disable=R0913
    wbs_l1: str,
    institution: types.DashVal,
    phds: types.DashVal,
    faculty: types.DashVal,
    sci: types.DashVal,
    grad: types.DashVal,
    cpus: types.DashVal,
    gpus: types.DashVal,
    text: str,
    hc_confirmed: bool,
    comp_confirmed: bool,
) -> None:
    """Push the institution's values."""
    _validate(wbs_l1, str, falsy_okay=False)
    institution = _validate(institution, types.DashVal_types)
    phds = _validate(phds, types.DashVal_types)
    faculty = _validate(faculty, types.DashVal_types)
    sci = _validate(sci, types.DashVal_types)
    grad = _validate(grad, types.DashVal_types)
    cpus = _validate(cpus, types.DashVal_types)
    gpus = _validate(gpus, types.DashVal_types)
    _validate(text, str)
    _validate(hc_confirmed, bool)
    _validate(comp_confirmed, bool)

    body = {"institution": institution}
    if phds or phds == 0:
        body["phds_authors"] = phds
    if faculty or faculty == 0:
        body["faculty"] = faculty
    if sci or sci == 0:
        body["scientists_post_docs"] = sci
    if grad or grad == 0:
        body["grad_students"] = grad
    if cpus or cpus == 0:
        body["cpus"] = cpus
    if gpus or gpus == 0:
        body["gpus"] = gpus
    body["text"] = text
    body["headcounts_confirmed"] = hc_confirmed
    body["computing_confirmed"] = comp_confirmed

    _ = mou_request("POST", f"/institution/values/{wbs_l1}", body=body)
