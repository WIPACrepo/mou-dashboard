"""Admin-only callbacks for a specified WBS layout."""


import logging
from typing import Dict, List, Optional, Tuple

import dash_bootstrap_components as dbc  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]
from flask_login import current_user  # type: ignore[import]

from ..config import app
from ..data_source import data_source as src
from ..data_source import table_config as tc
from ..data_source.utils import DataSourceException
from ..utils import dash_utils as du
from ..utils import types


def _get_ingest_sucess_message(
    n_records: int,
    prev_snap: Optional[types.SnapshotInfo],
    curr_snap: Optional[types.SnapshotInfo],
) -> List[str]:
    """Make the message for the ingest confirmation toast."""

    def _pseudonym(_snap: types.SnapshotInfo) -> str:
        if _snap["name"]:
            return f"\"{_snap['name']}\""
        return du.get_human_time(_snap["timestamp"])

    message = [
        f"Uploaded {n_records} records.",
        "A snapshot was made of:",
    ]

    if prev_snap:
        message.append(f"- the previous table ({_pseudonym(prev_snap)}) and")
    if curr_snap:
        message.append(f"- the current table ({_pseudonym(curr_snap)})")

    return message


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-upload-xlsx-modal", "is_open"),
        Output("wbs-upload-xlsx-filename-alert", "children"),
        Output("wbs-upload-xlsx-filename-alert", "color"),
        Output("wbs-upload-xlsx-override-table", "disabled"),
        Output("wbs-toast-via-upload-div", "children"),
    ],
    [
        Input("wbs-upload-xlsx-launch-modal-button", "n_clicks"),
        Input("wbs-upload-xlsx", "contents"),
        Input("wbs-upload-xlsx-cancel", "n_clicks"),
        Input("wbs-upload-xlsx-override-table", "n_clicks"),
    ],
    [State("wbs-current-l1", "value"), State("wbs-upload-xlsx", "filename")],
    prevent_initial_call=True,
)
def handle_xlsx(  # pylint: disable=R0911
    # input(s)
    _: int,
    contents: str,
    __: int,
    ___: int,
    # L1 value (state)
    wbs_l1: str,
    # other state(s)
    filename: str,
) -> Tuple[bool, str, str, bool, dbc.Toast]:
    """Manage uploading a new xlsx document as the new live table."""
    logging.warning(f"'{du.triggered_id()}' -> handle_xlsx()")

    if not current_user.is_authenticated or not current_user.is_admin:
        logging.error("Cannot handle xlsx since user is not admin.")
        return False, "", "", True, None

    if du.triggered_id() == "wbs-upload-xlsx-launch-modal-button":
        return True, "", "", True, None

    if du.triggered_id() == "wbs-upload-xlsx-cancel":
        return False, "", "", True, None

    if du.triggered_id() == "wbs-upload-xlsx":
        if not filename.endswith(".xlsx"):
            return (
                True,
                f'"{filename}" is not an .xlsx file',
                du.Color.DANGER,
                True,
                None,
            )
        return (
            True,
            f'Uploaded "{filename}"',
            du.Color.SUCCESS,
            False,
            None,
        )

    if du.triggered_id() == "wbs-upload-xlsx-override-table":
        base64_file = contents.split(",")[1]
        try:
            n_records, prev_snap, curr_snap = src.override_table(
                wbs_l1, base64_file, filename
            )
            success_toast = du.make_toast(
                f'Live types.Table Updated with "{filename}"',
                _get_ingest_sucess_message(n_records, prev_snap, curr_snap),
                du.Color.SUCCESS,
            )
            return False, "", "", True, success_toast
        except DataSourceException as e:
            error_message = f'Error overriding "{filename}" ({e})'
            return True, error_message, du.Color.DANGER, True, None

    raise Exception(f"Unaccounted for trigger {du.triggered_id()}")


@app.callback(  # type: ignore[misc]
    [Output("wbs-summary-table", "data"), Output("wbs-summary-table", "columns")],
    [Input("wbs-summary-table-recalculate", "n_clicks")],
    [
        State("wbs-current-l1", "value"),
        State("wbs-table-config-cache", "data"),
        State("wbs-current-snapshot-ts", "value"),
    ],
    prevent_initial_call=True,
)
def summarize(
    # input(s)
    _: int,
    # state(s)
    wbs_l1: str,
    state_tconfig_cache: tc.TableConfigParser.Cache,
    state_snap_current_ts: types.DDValue,
) -> Tuple[types.Table, List[Dict[str, str]]]:
    """Manage uploading a new xlsx document as the new live table."""
    logging.warning(f"'{du.triggered_id()}' -> summarize()")

    try:
        data_table = src.pull_data_table(wbs_l1)
    except DataSourceException:
        return [], []

    tconfig = tc.TableConfigParser(state_tconfig_cache)

    columns = [
        {"id": c, "name": c}
        for c in [
            "Institution",
            "Institutional Lead",
            "Ph.D. Authors",
            "Faculty",
            "Scientists / Post Docs",
            "Ph.D. Students",
            "WBS 2.1 Program Management",
            "WBS 2.2 Detector Operations & Maintenance",
            "WBS 2.3 Computing & Data Management",
            "WBS 2.4 Data Processing & Simulation",
            "WBS 2.5 Software",
            "WBS 2.6 Calibration",
            "Total",
        ]
    ]

    def _sum_it(_inst: str, _l2: str = "") -> float:
        return sum(
            float(r["FTE"])
            for r in data_table
            if r
            and r["FTE"]  # skip blanks (also 0s)
            and r["Institution"] == _inst
            and (not _l2 or r["WBS L2"] == _l2)
        )

    summary_table: types.Table = []
    for inst_full, abbrev in tconfig.get_institutions_w_abbrevs():
        inst_info = src.pull_institution_values(wbs_l1, state_snap_current_ts, abbrev)
        summary_table.append(
            {
                "Institution": inst_full,
                "Ph.D. Authors": inst_info["phds_authors"],
                "Faculty": inst_info["faculty"],
                "Scientists / Post Docs": inst_info["scientists_post_docs"],
                "Ph.D. Students": inst_info["grad_students"],
                "WBS 2.1 Program Management": _sum_it(
                    abbrev, "2.1 Program Coordination"
                ),
                "WBS 2.2 Detector Operations & Maintenance": _sum_it(
                    abbrev, "2.2 Detector Operations & Maintenance (Online)"
                ),
                "WBS 2.3 Computing & Data Management": _sum_it(
                    abbrev, "2.3 Computing & Data Management Services"
                ),
                "WBS 2.4 Data Processing & Simulation": _sum_it(
                    abbrev, "2.4 Data Processing & Simulation Services"
                ),
                "WBS 2.5 Software": _sum_it(abbrev, "2.5 Software"),
                "WBS 2.6 Calibration": _sum_it(abbrev, "2.6 Calibration"),
                "Total": _sum_it(abbrev),
            }
        )

    return summary_table, columns
