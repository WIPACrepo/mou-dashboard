"""Admin-only callbacks for a specified WBS layout."""

import logging
from collections import OrderedDict as ODict
from decimal import Decimal
from typing import Dict, Final, List, Optional, Tuple, TypedDict

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]
from flask_login import current_user  # type: ignore[import]

from ..config import app
from ..data_source import data_source as src
from ..data_source import table_config as tc
from ..data_source.utils import DataSourceException
from ..utils import dash_utils as du
from ..utils import types, utils

_CHANGES_COL: Final[str] = "Changes"


class _SnapshotBundle(TypedDict):
    table: types.Table
    info: types.SnapshotInfo


def _get_upload_success_modal_body(
    filename: str,
    n_records: int,
    prev_snap_info: Optional[types.SnapshotInfo],
    curr_snap_info: Optional[types.SnapshotInfo],
) -> List[dcc.Markdown]:
    """Make the message for the ingest confirmation toast."""

    def _pseudonym(_snap: types.SnapshotInfo) -> str:
        if _snap["name"]:
            return f"\"{_snap['name']}\""
        return utils.get_human_time(_snap["timestamp"])

    body: List[dcc.Markdown] = [
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
    Output("refresh-for-override-success", "run"),
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
) -> Tuple[bool, str, str, bool, dbc.Toast, bool, List[dcc.Markdown]]:
    """Manage uploading a new xlsx document as the new live table."""
    logging.warning(f"'{du.triggered_id()}' -> handle_xlsx()")

    if not current_user.is_authenticated or not current_user.is_admin:
        logging.error("Cannot handle xlsx since user is not admin.")
        return False, "", "", True, None, False, []

    if du.triggered_id() == "wbs-upload-xlsx-launch-modal-button":
        return True, "", "", True, None, False, []

    if du.triggered_id() == "wbs-upload-xlsx-cancel":
        return False, "", "", True, None, False, []

    if du.triggered_id() == "wbs-upload-xlsx":
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
        return True, f'Staged "{s_filename}"', du.Color.SUCCESS, False, None, False, []

    if du.triggered_id() == "wbs-upload-xlsx-override-table":
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

    raise Exception(f"Unaccounted for trigger {du.triggered_id()}")


@app.callback(  # type: ignore[misc]
    [Output("wbs-summary-table", "data"), Output("wbs-summary-table", "columns")],
    [Input("wbs-summary-table-recalculate", "n_clicks")],  # user-only
    [
        State("url", "pathname"),
        State("wbs-table-config-cache", "data"),
        State("wbs-current-snapshot-ts", "value"),
    ],
    prevent_initial_call=True,
)  # pylint: disable=R0914
def summarize(
    # input(s)
    _: int,
    # state(s)
    s_urlpath: str,
    s_tconfig_cache: tc.TableConfigParser.CacheType,
    s_snap_ts: types.DashVal,
) -> Tuple[types.Table, List[Dict[str, str]]]:
    """Manage uploading a new xlsx document as the new live table."""
    logging.warning(f"'{du.triggered_id()}' -> summarize()")

    assert not s_snap_ts

    wbs_l1 = du.get_wbs_l1(s_urlpath)
    tconfig = tc.TableConfigParser(wbs_l1, cache=s_tconfig_cache)

    try:
        data_table = src.pull_data_table(wbs_l1, tconfig)
    except DataSourceException:
        return [], []

    column_names = [
        "Institution",
        "Institutional Lead",
        "Ph.D. Authors",
        "Faculty",
        "Scientists / Post Docs",
        "Ph.D. Students",
    ]
    column_names.extend(tconfig.get_l2_categories())
    column_names.append("Total")
    columns = [{"id": c, "name": c, "type": "numeric"} for c in column_names]

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

    summary_table: types.Table = []
    for inst_full, abbrev in tconfig.get_institutions_w_abbrevs():
        phds, faculty, sci, grad, __ = src.pull_institution_values(
            wbs_l1, s_snap_ts, abbrev
        )

        row: Dict[str, types.StrNum] = {
            "Institution": inst_full,
            "Ph.D. Authors": phds if phds else 0,
            "Faculty": faculty if faculty else 0,
            "Scientists / Post Docs": sci if sci else 0,
            "Ph.D. Students": grad if grad else 0,
        }

        row.update({l2: _sum_it(abbrev, l2) for l2 in tconfig.get_l2_categories()})

        row["Total"] = _sum_it(abbrev)

        summary_table.append(row)

    return summary_table, columns


def _blame_row(
    record: types.Record,
    tconfig: tc.TableConfigParser,
    column_names: List[str],
    snap_bundles: Dict[str, _SnapshotBundle],
) -> types.Record:
    """Get the blame row for a record."""

    def _get_field_value_in_snap(bundle: _SnapshotBundle, field: str) -> types.StrNum:
        try:
            return next(
                r
                for r in bundle["table"]
                if r[tconfig.const.ID] == record[tconfig.const.ID]
            )[field]
        except StopIteration:
            return "no-value"

    # get each field's history; Schema: { <field>: {<snap_ts>:<field_value>} }
    field_changes: Dict[str, Dict[str, types.StrNum]] = {}
    field_changes = ODict({k: ODict({"today": record[k]}) for k in record})
    for snap_ts, bundle in snap_bundles.items():
        for field in record:
            field_changes[field][snap_ts] = _get_field_value_in_snap(bundle, field)

    # throw out fields that have never changed
    for field in field_changes:
        if len(set(field_changes[field].values())) < 2:
            field_changes[field] = {}

    # make markdown for cell
    markdown = ""
    for field, changes in field_changes.items():
        if not changes:
            continue
        markdown += f"\n**{field}**\n"
        for snap_ts, snap_val in changes.items():
            if field == tconfig.const.TIMESTAMP:
                snap_val = utils.get_human_time(str(snap_val))
            snap_val = f"`{snap_val}`" if snap_val else "*none*"
            markdown += f"- {snap_val}\n"
            if snap_ts == "today":
                markdown += "    + today\n"
                markdown += f"    + {utils.get_human_now()}\n"
            else:
                snap_time = utils.get_human_time(str(snap_ts))
                name = snap_bundles[snap_ts]["info"]["name"]
                markdown += f"    + {name}\n"
                markdown += f"    + {snap_time}\n"

    if not markdown:
        markdown = "*no changes*"

    blame_row = {k: v for k, v in record.items() if k in column_names}
    blame_row[_CHANGES_COL] = markdown
    return blame_row


def _blame_columns(column_names: List[str]) -> List[Dict[str, str]]:
    return [
        {
            "id": c,
            "name": c,
            "type": "text",
            "presentation": "markdown" if c == _CHANGES_COL else "input",
        }
        for c in column_names
    ]


def _blame_style_cell_conditional(column_names: List[str]) -> types.TSCCond:
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
        State("wbs-table-config-cache", "data"),
        State("wbs-current-snapshot-ts", "value"),
    ],
    prevent_initial_call=True,
)  # pylint: disable=R0914
def blame(
    # input(s)
    _: int,
    # state(s)
    s_urlpath: str,
    s_tconfig_cache: tc.TableConfigParser.CacheType,
    s_snap_ts: types.DashVal,
) -> Tuple[types.Table, List[Dict[str, str]], types.TSCCond]:
    """Manage uploading a new xlsx document as the new live table."""
    logging.warning(f"'{du.triggered_id()}' -> summarize()")

    assert not s_snap_ts

    # setup
    wbs_l1 = du.get_wbs_l1(s_urlpath)
    tconfig = tc.TableConfigParser(wbs_l1, cache=s_tconfig_cache)

    try:
        data_table = src.pull_data_table(wbs_l1, tconfig, raw=True)
        data_table.sort(
            key=lambda r: r[tconfig.const.TIMESTAMP], reverse=True,
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
    snap_bundles: Dict[str, _SnapshotBundle] = {
        info["timestamp"]: {
            "table": src.pull_data_table(
                wbs_l1, tconfig, snapshot_ts=info["timestamp"], raw=True,
            ),
            "info": info,
        }
        for info in src.list_snapshots(wbs_l1)
    }
    blame_table = [
        _blame_row(r, tconfig, column_names, snap_bundles) for r in data_table
    ]

    return (
        blame_table,
        _blame_columns(column_names),
        _blame_style_cell_conditional(column_names),
    )
