"""Admin-only callbacks for a specified WBS layout."""  # lgtm [py/syntax-error]

import dataclasses as dc
import logging
from collections import OrderedDict as ODict
from decimal import Decimal
from typing import Any, Final, cast

import dash_bootstrap_components as dbc  # type: ignore[import]
import universal_utils.types as uut
from dash import dcc, no_update  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]

from ..config import app
from ..data_source import connections
from ..data_source import data_source as src
from ..data_source import table_config as tc
from ..data_source.connections import CurrentUser, DataSourceException
from ..utils import dash_utils as du
from ..utils import types, utils

_CHANGES_COL: Final[str] = "Changes"


@dc.dataclass(frozen=True)
class _SnapshotBundle:
    table: uut.WebTable
    info: uut.SnapshotInfo


def _get_upload_success_modal_body(
    filename: str,
    n_records: int,
    prev_snap_info: uut.SnapshotInfo | None,
    curr_snap_info: uut.SnapshotInfo | None,
) -> list[dcc.Markdown]:
    """Make the message for the ingest confirmation toast."""

    def _pseudonym(snapinfo: uut.SnapshotInfo) -> str:
        if snapinfo.name:
            return f'"{snapinfo.name}"'
        return utils.get_human_time(snapinfo.timestamp)

    body: list[dcc.Markdown] = [
        dcc.Markdown(f'Uploaded {n_records} rows from "{filename}".'),
        dcc.Markdown("A snapshot was made of:"),
    ]

    if prev_snap_info:
        body.append(
            dcc.Markdown(f"- the previous table ({_pseudonym(prev_snap_info)}) and")
        )
    if curr_snap_info:
        body.append(dcc.Markdown(f"- the current table ({_pseudonym(curr_snap_info)})"))

    body.append(
        dcc.Markdown(
            "Each institution's headcounts and notes were also copied forward."
        )
    )

    return body


@app.callback(  # type: ignore[misc]
    Output("reload-for-override-success", "run"),
    [Input("wbs-upload-success-view-new-table-button", "n_clicks")],  # user-only
    prevent_initial_call=True,
)
def refresh_for_override_success(_: int) -> str:
    """Refresh page for to view new live table."""
    return du.RELOAD


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-upload-xlsx-modal", "is_open"),
        Output("wbs-upload-xlsx-filename-alert", "children"),
        Output("wbs-upload-xlsx-filename-alert", "color"),
        Output("wbs-upload-xlsx-override-table", "disabled"),
        Output("wbs-toast-via-upload-div", "children"),
        Output("wbs-upload-success-modal", "is_open"),
        Output("wbs-upload-success-modal-body", "children"),
    ],
    [
        Input("wbs-upload-xlsx-launch-modal-button", "n_clicks"),  # user-only
        Input("wbs-upload-xlsx", "contents"),  # user-only
        Input("wbs-upload-xlsx-cancel", "n_clicks"),  # user-only
        Input("wbs-upload-xlsx-override-table", "n_clicks"),  # user-only
    ],
    [State("url", "pathname"), State("wbs-upload-xlsx", "filename")],
    prevent_initial_call=True,
)
def handle_xlsx(  # pylint: disable=R0911
    # input(s)
    _: int,
    contents: str,
    __: int,
    ___: int,
    # state(s)
    s_urlpath: str,
    s_filename: str,
) -> tuple[bool, str, str, bool, dbc.Toast, bool, list[dcc.Markdown]]:
    """Manage uploading a new xlsx document as the new live table."""
    logging.warning(f"'{du.triggered()}' -> handle_xlsx()")

    if not CurrentUser.is_loggedin_with_permissions() or not CurrentUser.is_admin():
        logging.error("Cannot handle xlsx since user is not admin.")
        return False, "", "", True, None, False, []

    match du.triggered():
        # Launch xlsx
        case "wbs-upload-xlsx-launch-modal-button.n_clicks":
            return True, "", "", True, None, False, []
        # Cancel upload xlsx
        case "wbs-upload-xlsx-cancel.n_clicks":
            return False, "", "", True, None, False, []
        # Upload xlsx
        case "wbs-upload-xlsx.contents":
            if not s_filename.endswith(".xlsx"):
                return (
                    True,
                    f'"{s_filename}" is not an .xlsx file',
                    du.Color.DANGER,
                    True,
                    None,
                    False,
                    [],
                )
            return (
                True,
                f'Staged "{s_filename}"',
                du.Color.SUCCESS,
                False,
                None,
                False,
                [],
            )
        # Override xlsx
        case "wbs-upload-xlsx-override-table.n_clicks":
            base64_file = contents.split(",")[1]
            try:
                n_records, prev_snap_info, curr_snap_info = src.override_table(
                    du.get_wbs_l1(s_urlpath), base64_file, s_filename
                )
                msg = _get_upload_success_modal_body(
                    s_filename, n_records, prev_snap_info, curr_snap_info
                )
                return False, "", "", True, None, True, msg
            except DataSourceException as e:
                error_message = f'Error overriding "{s_filename}" ({e})'
                return True, error_message, du.Color.DANGER, True, None, False, []

    raise Exception(f"Unaccounted for trigger {du.triggered()}")


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-summary-table", "data"),
        Output("wbs-summary-table", "columns"),
        Output("wbs-summary-table", "style_data_conditional"),
    ],
    [Input("wbs-summary-table-recalculate", "n_clicks")],  # user-only
    [
        State("url", "pathname"),
        State("wbs-current-snapshot-ts", "value"),
    ],
    prevent_initial_call=True,
)  # pylint: disable=R0914
def summarize(
    # input(s)
    _: int,
    # state(s)
    s_urlpath: str,
    s_snap_ts: types.DashVal,
) -> tuple[uut.WebTable, list[dict[str, str]], list[dict[str, Any]]]:
    """Manage uploading a new xlsx document as the new live table."""
    logging.warning(f"'{du.triggered()}' -> summarize()")

    wbs_l1 = du.get_wbs_l1(s_urlpath)
    tconfig = tc.TableConfigParser(wbs_l1)

    try:
        data_table = src.pull_data_table(wbs_l1, tconfig, snapshot_ts=s_snap_ts)
    except DataSourceException:
        return [], [], []

    insts_infos = connections.get_todays_institutions_infos()

    def _sum_it(_inst: str, _l2: str = "") -> float:
        return float(
            sum(
                Decimal(str(r["FTE"]))  # avoid floating point loss
                for r in data_table
                if r
                and r["FTE"]  # skip blanks (also 0s)
                and r["Institution"] == _inst
                and (not _l2 or r["WBS L2"] == _l2)
            )
        )

    summary_table: uut.WebTable = []
    for short_name, inst_info in insts_infos.items():
        inst_dc = src.pull_institution_values(wbs_l1, s_snap_ts, short_name)

        row: dict[str, uut.StrNum] = {
            "Institution": inst_info.long_name,
            "Institutional Lead": inst_info.institution_lead_uid,
            "SOW Table Confirmed": (
                f"{utils.get_human_time(str(inst_dc.table_metadata.confirmation_ts), short=True)}"
                f"{'' if inst_dc.table_metadata.has_valid_confirmation() else ' ('+inst_dc.table_metadata.get_confirmation_reason()+')'}"
            ),
        }

        if wbs_l1 == "mo":
            row.update(
                {
                    "Ph.D. Authors": inst_dc.phds_authors
                    if inst_dc.phds_authors
                    else 0,
                    "Faculty": inst_dc.faculty if inst_dc.faculty else 0,
                    "Scientists / Post Docs": inst_dc.scientists_post_docs
                    if inst_dc.scientists_post_docs
                    else 0,
                    "Ph.D. Students": inst_dc.grad_students
                    if inst_dc.grad_students
                    else 0,
                    "Headcounts Confirmed": (
                        f"{utils.get_human_time(str(inst_dc.headcounts_metadata.confirmation_ts), short=True)}"
                        f"{'' if inst_dc.headcounts_metadata.has_valid_confirmation() else ' ('+inst_dc.headcounts_metadata.get_confirmation_reason()+')'}"
                    ),
                    "CPU": inst_dc.cpus if inst_dc.cpus else 0,
                    "GPU": inst_dc.gpus if inst_dc.gpus else 0,
                    "Computing Confirmed": (
                        f"{utils.get_human_time(str(inst_dc.computing_metadata.confirmation_ts), short=True)}"
                        f"{'' if inst_dc.computing_metadata.has_valid_confirmation() else ' ('+inst_dc.computing_metadata.get_confirmation_reason()+')'}"
                    ),
                }
            )
            row["Headcount Total"] = sum(
                cast(float, row.get(hc))
                for hc in ["Faculty", "Scientists / Post Docs", "Ph.D. Students"]
            )

        row.update({l2: _sum_it(short_name, l2) for l2 in tconfig.get_l2_categories()})

        row["FTE Total"] = _sum_it(short_name)

        if wbs_l1 == "mo":
            try:
                row["FTE / Headcount"] = cast(float, row["FTE Total"]) / cast(
                    float, row["Headcount Total"]
                )
            except ZeroDivisionError:
                row["FTE / Headcount"] = "-"

            row["Notes"] = inst_dc.text

        summary_table.append(row)

    columns = summary_table[0].keys()
    style_data_conditional = [
        {
            "if": {
                "filter_query": f'{{{col}}} contains "({uut.CHANGES})" or {{{col}}} contains "({uut.EXPIRED})"'
            },
            "backgroundColor": du.LIGHT_YELLOW,
        }
        for col in columns
    ]

    return (
        summary_table,
        [{"id": c, "name": c, "type": "numeric"} for c in columns],
        style_data_conditional,
    )


def _blame_row(
    record: uut.WebRecord,
    tconfig: tc.TableConfigParser,
    column_names: list[str],
    snap_bundles: dict[str, _SnapshotBundle],
) -> uut.WebRecord:
    """Get the blame row for a record."""
    logging.info(f"Blaming {record[tconfig.const.ID]}...")

    NA: Final[str] = "n/a"  # pylint: disable=C0103
    MOST_RECENT_VALUE: Final[str] = "today"  # pylint: disable=C0103

    def _find_record_in_snap(table: uut.WebTable) -> uut.WebRecord | None:
        try:
            return next(
                r for r in table if r[tconfig.const.ID] == record[tconfig.const.ID]
            )
        except StopIteration:
            return None

    # get each field's history; Schema: { <field>: {<snap_ts>:<field_value>} }
    field_changes: dict[str, dict[str, uut.StrNum]] = {}
    field_changes = ODict({k: ODict({MOST_RECENT_VALUE: record[k]}) for k in record})
    brand_new, never_changed, oldest_snap_ts = True, True, ""
    for snap_ts, bundle in snap_bundles.items():
        if snap_record := _find_record_in_snap(bundle.table):
            brand_new = False
        for field in record:
            if field in ["", tconfig.const.GRAND_TOTAL, tconfig.const.US_NON_US]:
                continue
            if (not snap_record) or (field not in snap_record):
                field_changes[field][snap_ts] = NA
            elif snap_record[field] != record[field]:
                field_changes[field][snap_ts] = snap_record[field]
                never_changed = False
            else:
                oldest_snap_ts = snap_ts

    # throw out fields that have never changed
    for field in field_changes:
        if len(set(field_changes[field].values())) < 2:
            field_changes[field] = {}
        # every old value is just NA
        elif all(v == NA for v in list(field_changes[field].values())[1:]):
            field_changes[field] = {}

    # set up markdown
    markdown = ""
    if brand_new:
        markdown = "***row is brand new***"
    elif never_changed:
        markdown = "**no changes since original snapshot:**\n"
        markdown += f"- {snap_bundles[oldest_snap_ts].info.name} ({utils.get_human_time(str(oldest_snap_ts), short=True)})"
    else:
        for field, changes in field_changes.items():
            if not changes:
                continue
            first_na = True
            # Field
            markdown += f"\n**{field}**\n"
            # Values over time
            for snap_ts, snap_val in changes.items():
                if snap_val == NA:
                    if first_na:
                        markdown += "    + **Original Snapshot's Value**\n"
                        first_na = False
                    continue
                # convert timestamps to be human-readable
                if field == tconfig.const.TIMESTAMP:
                    snap_val = utils.get_human_time(str(snap_val))
                # value
                markdown += f"- `{snap_val}`\n" if snap_val else "- *none*\n"
                # a current value
                if snap_ts == MOST_RECENT_VALUE:
                    markdown += (
                        f"    + **Current Value** ({utils.get_human_now(short=True)})\n"
                    )
                # a historical value
                else:
                    markdown += f"    + Snapshot: {snap_bundles[snap_ts].info.name} ({utils.get_human_time(str(snap_ts), short=True)})\n"

    blame_row = {k: v for k, v in record.items() if k in column_names}
    blame_row[_CHANGES_COL] = markdown
    return blame_row


def _blame_columns(column_names: list[str]) -> list[dict[str, str]]:
    return [
        {
            "id": c,
            "name": c,
            "type": "text",
            "presentation": "markdown" if c == _CHANGES_COL else "input",
        }
        for c in column_names
    ]


def _blame_style_cell_conditional(column_names: list[str]) -> types.TSCCond:
    style_cell_conditional = []
    # border-left
    for col in [_CHANGES_COL]:
        style_cell_conditional.append(
            {"if": {"column_id": col}, "border-left": f"2.5px solid {du.TABLE_GRAY}"}
        )
    # width
    widths = {_CHANGES_COL: "50"}
    default_width = "20"
    for col in column_names:
        style_cell_conditional.append(
            {
                "if": {"column_id": col},
                "minWidth": widths.get(col, default_width),
                "width": widths.get(col, default_width),
                "maxWidth": widths.get(col, default_width),
            }
        )
    return style_cell_conditional


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-blame-table", "data"),
        Output("wbs-blame-table", "columns"),
        Output("wbs-blame-table", "style_cell_conditional"),
    ],
    [Input("wbs-blame-table-button", "n_clicks")],  # user-only
    [
        State("url", "pathname"),
        State("wbs-current-snapshot-ts", "value"),
    ],
    prevent_initial_call=True,
)  # pylint: disable=R0914
def blame(
    # input(s)
    _: int,
    # state(s)
    s_urlpath: str,
    s_snap_ts: types.DashVal,
) -> tuple[uut.WebTable, list[dict[str, str]], types.TSCCond]:
    """Manage uploading a new xlsx document as the new live table."""
    logging.warning(f"'{du.triggered()}' -> summarize()")

    assert not s_snap_ts

    # setup
    wbs_l1 = du.get_wbs_l1(s_urlpath)
    tconfig = tc.TableConfigParser(wbs_l1)

    try:
        data_table = src.pull_data_table(wbs_l1, tconfig, raw=True)
        data_table.sort(
            key=lambda r: r[tconfig.const.TIMESTAMP],
            reverse=True,
        )
    except DataSourceException:
        return [], [], []

    column_names = [
        tconfig.const.WBS_L2,
        tconfig.const.WBS_L3,
        tconfig.const.INSTITUTION,
        tconfig.const.NAME,
        tconfig.const.SOURCE_OF_FUNDS_US_ONLY,
        _CHANGES_COL,
    ]

    # populate blame table
    snap_bundles: dict[str, _SnapshotBundle] = {
        si.timestamp: _SnapshotBundle(
            table=src.pull_data_table(
                wbs_l1,
                tconfig,
                snapshot_ts=si.timestamp,
                raw=True,
            ),
            info=si,
        )
        for si in src.list_snapshots(wbs_l1)
    }
    blame_table = [
        _blame_row(r, tconfig, column_names, snap_bundles) for r in data_table
    ]

    return (
        blame_table,
        _blame_columns(column_names),
        _blame_style_cell_conditional(column_names),
    )


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-retouchstone-button", "children"),
        Output("wbs-retouchstone-button", "disabled"),
        Output("reload-for-retouchstone", "run"),
    ],
    [Input("wbs-retouchstone-button", "n_clicks")],  # user-only
    [
        State("url", "pathname"),
        State("wbs-current-snapshot-ts", "value"),
    ],
    # prevent_initial_call=True,
)  # pylint: disable=R0914
def retouchstone(
    # input(s)
    _: int,
    # state(s)
    s_urlpath: str,
    s_snap_ts: types.DashVal,
) -> tuple[str, bool, str]:
    """Make an updated touchstone timestamp value."""
    logging.warning(f"'{du.triggered()}' -> summarize()")

    match du.triggered():
        # ON LOAD
        case ".":
            if s_snap_ts:
                return (
                    "Cannot reset institution confirmations for snapshots",
                    True,
                    no_update,
                )
            timestamp = src.get_touchstone(du.get_wbs_l1(s_urlpath))
            return (
                f"Reset Institution Confirmations ({utils.get_human_time(str(timestamp), medium=True)})",
                not CurrentUser.is_admin(),
                no_update,
            )
        # CLICKED
        case "wbs-retouchstone-button.n_clicks":
            timestamp = src.retouchstone(du.get_wbs_l1(s_urlpath))
            return (
                f"Reset Institution Confirmations ({utils.get_human_time(str(timestamp), medium=True)})",
                True,
                du.RELOAD,
            )

    raise Exception(f"Unaccounted for trigger {du.triggered()}")
