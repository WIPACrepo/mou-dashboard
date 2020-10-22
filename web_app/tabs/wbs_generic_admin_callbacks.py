"""Callbacks for a specified WBS layout."""


import logging
from typing import List, Optional, Tuple

import dash_bootstrap_components as dbc  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]
from flask_login import current_user  # type: ignore[import]

from ..config import app
from ..data_source import data_source as src
from ..data_source.utils import DataSourceException
from ..utils import dash_utils as du
from ..utils.types import SnapshotInfo


def _get_ingest_sucess_message(
    n_records: int, prev_snap: Optional[SnapshotInfo], curr_snap: Optional[SnapshotInfo]
) -> List[str]:
    """Make the message for the ingest confirmation toast."""

    def _pseudonym(_snap: SnapshotInfo) -> str:
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
        Output("wbs-refresh-button", "n_clicks"),
        Output("wbs-toast-via-upload-div", "children"),
    ],
    [
        Input("wbs-upload-xlsx-launch-modal-button", "n_clicks"),
        Input("wbs-upload-xlsx", "contents"),
        Input("wbs-upload-xlsx-cancel", "n_clicks"),
        Input("wbs-upload-xlsx-override-table", "n_clicks"),
    ],
    [State("wbs-l1", "value"), State("wbs-upload-xlsx", "filename")],
    prevent_initial_call=True,
)
def handle_xlsx(
    # input(s)
    _: int,
    contents: str,
    __: int,
    ___: int,
    # L1 value (state)
    wbs_l1: str,
    # other state(s)
    filename: str,
) -> Tuple[bool, str, str, bool, int, dbc.Toast]:
    """Manage uploading a new xlsx document as the new live table."""
    logging.warning("handle_xlsx()")

    if du.triggered_id() == "wbs-upload-xlsx-launch-modal-button":
        return True, "", "", True, 0, None

    if du.triggered_id() == "wbs-upload-xlsx-cancel":
        return False, "", "", True, 0, None

    if du.triggered_id() == "wbs-upload-xlsx":
        if not filename.endswith(".xlsx"):
            return (
                True,
                f'"{filename}" is not an .xlsx file',
                du.Color.DANGER,
                True,
                0,
                None,
            )
        return True, f'Uploaded "{filename}"', du.Color.SUCCESS, False, 0, None

    if du.triggered_id() == "wbs-upload-xlsx-override-table":
        base64_file = contents.split(",")[1]
        try:
            n_records, prev_snap, curr_snap = src.override_table(
                wbs_l1, base64_file, filename
            )
            success_toast = du.make_toast(
                f'Live Table Updated with "{filename}"',
                _get_ingest_sucess_message(n_records, prev_snap, curr_snap),
                du.Color.SUCCESS,
            )
            return False, "", "", True, 1, success_toast

        except DataSourceException as e:
            error_message = f'Error overriding "{filename}" ({e})'
            return True, error_message, du.Color.DANGER, True, 0, None

    raise Exception(f"Unaccounted for trigger {du.triggered_id()}")
