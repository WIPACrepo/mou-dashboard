"""REST interface for reading and writing MOU data."""


from typing import Any, Final, TypedDict, cast

import universal_utils.types as uut
from dacite import from_dict

from ..data_source.connections import CurrentUser
from ..utils import types, utils
from . import table_config as tc
from .connections import mou_request

# constants
_OC_SUFFIX: Final[str] = "_original"


# --------------------------------------------------------------------------------------
# Data/uut.WebTable-Conversion Functions


def get_touchstone_name(column: str) -> str:
    """Return the column name for detecting changed data.

    For use as an "if" value in a DataTable.style_data_conditional
    entry's filter query.
    """
    return f"{column}{_OC_SUFFIX}"


def _is_touchstone_column(column: str) -> bool:
    return column.endswith(_OC_SUFFIX)


def _convert_record_rest_to_dash(
    record: uut.WebRecord, tconfig: tc.TableConfigParser, novel: bool = False
) -> uut.WebRecord:
    """Convert a record to be added to Dash's datatable.

    Make a copy of each field in an new column to detect changed values.
    These columns aren't meant to be seen by the user.

    Arguments:
        record {uut.WebRecord} -- the record, that will be updated

    Keyword Arguments:
        novel {bool} -- if True, don't copy values, just set as '' (default: {False})

    Returns:
        uut.WebRecord -- the argument value
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
    table: uut.WebTable, tconfig: tc.TableConfigParser
) -> uut.WebTable:
    """Convert a table to be added as Dash's datatable.

    Make a copy of each column to detect changed values (aka the
    touchstone column). Hide these touchstone columns by not adding them
    to the Dash's datatable's `columns` property.
    """
    for record in table:
        _convert_record_rest_to_dash(record, tconfig)

    return table


def _is_valid_simple_dropdown(
    parser: tc.TableConfigParser, record: uut.WebRecord, field: str
) -> bool:
    if not parser.is_simple_dropdown(field):
        raise Exception(f"not simple dropdown: {field} ({record})")

    if record[field] not in parser.get_simple_column_dropdown_menu(field):
        return False

    return True


def _is_valid_conditional_dropdown(
    parser: tc.TableConfigParser, record: uut.WebRecord, field: str
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
    record: uut.WebRecord, tconfig: tc.TableConfigParser
) -> uut.WebRecord:
    """Remove items whose data aren't valid."""

    def _remove_orphans(_record: uut.WebRecord) -> uut.WebRecord:
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
    record: uut.WebRecord, tconfig: tc.TableConfigParser | None = None
) -> uut.WebRecord:
    """Convert a record from Dash's datatable to be sent to the rest server.

    Copy but leave out the touchstone columns used to detect changed
    values.
    """
    out_record = {k: v for k, v in record.items() if not _is_touchstone_column(k)}

    if tconfig:
        out_record = _remove_invalid_data(out_record, tconfig)

    return out_record


def record_to_strings(
    record: uut.WebRecord, tconfig: tc.TableConfigParser
) -> list[str]:
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
    in_type: type | tuple[type, ...],
    falsy_okay: bool = True,
    out: type | None = None,
) -> Any:
    """Type-check `data`. Optionally, convert and return.

    Arguments:
        `data`
            data to be validated
        `in_type`
            allowed type(s)

    Keyword Arguments:
        `falsy_okay`
            otherwise, raise `TypeError` if `not data` (default: {True})
        `out`
            assure `data`'s returned type, AND assign `out`'s default falsy value (if `not data`) (default: {None})

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
# Table/Record Functions


def pull_data_table(  # pylint: disable=R0913
    wbs_l1: str,
    tconfig: tc.TableConfigParser,
    institution: types.DashVal = "",
    with_totals: bool = False,
    snapshot_ts: types.DashVal = "",
    restore_id: str = "",
    raw: bool = False,
) -> uut.WebTable:
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
        uut.WebTable -- the returned table
    """
    _validate(wbs_l1, str, falsy_okay=False)
    institution = _validate(institution, types.DashVal_types, out=str)
    # labor = _validate(labor, types.DashVal_types, out=str)
    _validate(with_totals, bool)
    snapshot_ts = _validate(snapshot_ts, types.DashVal_types, out=str)
    _validate(restore_id, str)

    class _RespTableData(TypedDict):
        table: uut.WebTable

    # request
    body = {
        "institution": institution,
        "total_rows": with_totals,
        "snapshot": snapshot_ts,
        "restore_id": restore_id,
    }

    response = cast(
        _RespTableData,
        mou_request("GET", f"/table/data/{wbs_l1}", body=body),
    )
    # get & convert
    if raw:
        return response["table"]
    return _convert_table_rest_to_dash(response["table"], tconfig)


def push_record(  # pylint: disable=R0913
    wbs_l1: str,
    record: uut.WebRecord,
    tconfig: tc.TableConfigParser,
    # task: str = "",
    institution: types.DashVal = "",
    novel: bool = False,
) -> uut.WebRecord:
    """Push new/changed record to source.

    Keyword Arguments:
        institution {str} -- institution value to be inserted into record (default: {""})
        novel {bool} -- whether the record is new (default: {False})

    Returns:
        uut.WebRecord -- the returned record
    """
    _validate(wbs_l1, str, falsy_okay=False)
    _validate(record, dict)
    # _validate(task, str)

    institution = _validate(institution, types.DashVal_types, out=str)
    _validate(novel, bool)
    _validate(tconfig, tc.TableConfigParser)

    if institution:
        record[tconfig.const.INSTITUTION] = institution

    class _RespRecord(TypedDict):
        record: uut.WebRecord
        institution_values: uut.InstitutionValues

    # request
    body: dict[str, Any] = {
        "record": _convert_record_dash_to_rest(record, tconfig),
        "editor": CurrentUser.get_username(),
    }

    # if task:
    #     body["task"] = task.replace("\n", " ")
    response = cast(_RespRecord, mou_request("POST", f"/record/{wbs_l1}", body=body))
    # get & convert
    return _convert_record_rest_to_dash(response["record"], tconfig, novel=novel)


def delete_record(wbs_l1: str, record_id: str) -> None:
    """Delete the record, return True if successful."""
    _validate(wbs_l1, str, falsy_okay=False)
    _validate(record_id, str)

    body = {
        "record_id": record_id,
        "editor": CurrentUser.get_username(),
    }
    mou_request("DELETE", f"/record/{wbs_l1}", body=body)


# --------------------------------------------------------------------------------------
# Snapshot Functions


def list_snapshots(wbs_l1: str) -> list[uut.SnapshotInfo]:
    """Get the list of snapshots."""
    _validate(wbs_l1, str, falsy_okay=False)

    class _RespSnapshots(TypedDict):
        snapshots: list[dict]  # to be list[uut.SnapshotInfo]

    body = {
        "is_admin": CurrentUser.is_loggedin_with_permissions()
        and CurrentUser.is_admin()
    }
    response = cast(
        _RespSnapshots, mou_request("GET", f"/snapshots/list/{wbs_l1}", body)
    )

    return sorted(
        [uut.SnapshotInfo(**s) for s in response["snapshots"]],
        key=lambda si: si.timestamp,
        reverse=True,
    )


def create_snapshot(wbs_l1: str, name: str) -> uut.SnapshotInfo:
    """Create a snapshot."""
    _validate(wbs_l1, str, falsy_okay=False)
    _validate(name, str)

    body = {
        "creator": CurrentUser.get_username(),
        "name": name,
    }
    response = mou_request("POST", f"/snapshots/make/{wbs_l1}", body=body)
    return uut.SnapshotInfo(**response)


# --------------------------------------------------------------------------------------
# Table-Override Functions


def override_table(
    wbs_l1: str, base64_file: str, filename: str
) -> tuple[int, uut.SnapshotInfo | None, uut.SnapshotInfo]:
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
        previous_snapshot: dict | None  # to be uut.SnapshotInfo
        current_snapshot: dict  # to be uut.SnapshotInfo

    body = {
        "base64_file": base64_file,
        "filename": filename,
        "creator": CurrentUser.get_username(),
    }
    response = cast(
        _RespTableData,
        mou_request("POST", f"/table/data/{wbs_l1}", body=body),
    )
    return (
        response["n_records"],
        None
        if not response["previous_snapshot"]
        else uut.SnapshotInfo(**response["previous_snapshot"]),
        uut.SnapshotInfo(**response["current_snapshot"]),
    )


# --------------------------------------------------------------------------------------
# Institution-Value Functions


def pull_institution_values(
    wbs_l1: str, snapshot_ts: types.DashVal, institution: types.DashVal
) -> uut.InstitutionValues:
    """Get the institution's values."""
    _validate(wbs_l1, str, falsy_okay=False)
    snapshot_ts = _validate(snapshot_ts, types.DashVal_types, out=str)
    institution = _validate(institution, types.DashVal_types, out=str)

    body = {
        "institution": institution,
        "snapshot_timestamp": snapshot_ts,
    }
    response = mou_request("GET", f"/institution/values/{wbs_l1}", body=body)
    return from_dict(uut.InstitutionValues, response)  # type: ignore[no-any-return] # fixed in future release


def push_institution_values(  # pylint: disable=R0913
    wbs_l1: str,
    institution: types.DashVal,
    inst_dc: uut.InstitutionValues,
) -> uut.InstitutionValues:
    """Push the institution's values."""
    _validate(wbs_l1, str, falsy_okay=False)
    institution = _validate(institution, types.DashVal_types)

    response = mou_request(
        "POST",
        f"/institution/values/{wbs_l1}",
        body=inst_dc.restful_dict(institution),  # type: ignore[arg-type]
    )
    return from_dict(uut.InstitutionValues, response)  # type: ignore[no-any-return] # fixed in future release


def confirm_institution_values(
    wbs_l1: str,
    institution: str,
    headcounts: bool = False,
    table: bool = False,
    computing: bool = False,
) -> uut.InstitutionValues:
    """Confirm the institution's indicated values."""
    _validate(wbs_l1, str, falsy_okay=False)
    institution = _validate(institution, types.DashVal_types, out=str)

    response = mou_request(
        "POST",
        f"/institution/values/confirmation/{wbs_l1}",
        body={
            "institution": institution,
            "headcounts": headcounts,
            "table": table,
            "computing": computing,
        },
    )
    return from_dict(uut.InstitutionValues, response)  # type: ignore[no-any-return] # fixed in future release


def retouchstone(wbs_l1: str) -> int:
    """Make an updated touchstone timestamp value for all institutions (no
    snapshots)."""
    _validate(wbs_l1, str, falsy_okay=False)

    response = mou_request(
        "POST", f"/institution/values/confirmation/touchstone/{wbs_l1}"
    )
    return response["touchstone_timestamp"]  # type: ignore[no-any-return]


def get_touchstone(wbs_l1: str) -> int:
    """Make an updated touchstone timestamp value for all institutions (no
    snapshots)."""
    _validate(wbs_l1, str, falsy_okay=False)

    response = mou_request(
        "GET", f"/institution/values/confirmation/touchstone/{wbs_l1}"
    )
    return response["touchstone_timestamp"]  # type: ignore[no-any-return]
