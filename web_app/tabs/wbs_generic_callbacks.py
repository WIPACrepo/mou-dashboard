"""Callbacks for a specified WBS layout."""

import logging
import re
from typing import cast, Dict, List, Tuple, Union

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_html_components as html  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]
from flask_login import current_user  # type: ignore[import]

from ..config import app
from ..data_source import data_source as src
from ..data_source import table_config as tc
from ..data_source.utils import DataSourceException
from ..utils import dash_utils as du
from ..utils import types

# --------------------------------------------------------------------------------------
# types.Table Callbacks


def _totals_button_logic(
    n_clicks: int, state_all_cols: int
) -> Tuple[bool, str, str, bool, int]:
    """Figure out whether to include totals, and format the button.

    Returns:
        bool -- whether to include totals
        str  -- button label
        str  -- button color
        bool -- button outline
        int  -- auto n_clicks for "wbs-show-all-columns-button"
    """
    on = n_clicks % 2 == 1  # pylint: disable=C0103
    triggered = du.triggered_id() == "wbs-show-totals-button"

    if not on:  # off -> don't trigger "show-all-columns"
        return False, "Show Totals", du.Color.SECONDARY, True, state_all_cols

    if triggered:  # on and triggered -> trigger "show-all-columns"
        return True, "Hide Totals", du.Color.DARK, False, 1

    # on and not triggered, AKA already on -> don't trigger "show-all-columns"
    return True, "Hide Totals", du.Color.DARK, False, state_all_cols


def _add_new_data(  # pylint: disable=R0913
    wbs_l1: str,
    state_table: types.Table,
    state_columns: types.TColumns,
    labor: types.DDValue,
    institution: types.DDValue,
    state_tconfig_cache: tc.TableConfigParser.Cache,
) -> Tuple[types.Table, dbc.Toast]:
    """Push new record to data source; add to table.

    Returns:
        TData     -- up-to-date data table
        dbc.Toast -- toast element with confirmation message
    """
    table = state_table
    column_names = [c["name"] for c in state_columns]
    new_record: types.Record = {n: "" for n in column_names}

    # push to data source AND auto-fill labor and/or institution
    try:
        new_record = src.push_record(
            wbs_l1,
            new_record,
            labor=labor,
            institution=institution,
            novel=True,
            tconfig_cache=state_tconfig_cache,
        )
        table.insert(0, new_record)
        toast = du.make_toast(
            "types.Record Added", f"id: {new_record[src.ID]}", du.Color.SUCCESS, 5
        )
    except DataSourceException:
        toast = du.make_toast(
            "Failed to Make types.Record", du.REFRESH_MSG, du.Color.DANGER
        )

    return table, toast


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-data-table", "data"),
        Output("wbs-data-table", "page_current"),
        Output("wbs-table-exterior-control-last-timestamp", "data"),
        Output("wbs-toast-via-exterior-control-div", "children"),
        Output("wbs-show-totals-button", "children"),
        Output("wbs-show-totals-button", "color"),
        Output("wbs-show-totals-button", "outline"),
        Output("wbs-show-all-columns-button", "n_clicks"),
    ],
    [
        Input("wbs-current-institution", "value"),
        Input("wbs-filter-labor", "value"),
        Input("wbs-new-data-button-1", "n_clicks"),
        Input("wbs-new-data-button-2", "n_clicks"),
        Input("wbs-show-totals-button", "n_clicks"),
        Input("wbs-undo-last-delete", "n_clicks"),
    ],
    [
        State("wbs-current-l1", "value"),
        State("wbs-current-snapshot-ts", "value"),
        State("wbs-data-table", "data"),
        State("wbs-data-table", "columns"),
        State("wbs-show-all-columns-button", "n_clicks"),
        State("wbs-last-deleted-id", "children"),
        State("wbs-table-config-cache", "data"),
    ],
    prevent_initial_call=True,  # must wait for institution value
)  # pylint: disable=R0913,R0914
def table_data_exterior_controls(
    # input(s)
    institution: types.DDValue,
    labor: types.DDValue,
    _: int,
    tot_n_clicks: int,
    __: int,
    ___: int,
    # L1 (state)
    wbs_l1: str,
    # state(s)
    state_snapshot_ts: types.DDValue,
    state_table: types.Table,
    state_columns: types.TColumns,
    state_all_cols: int,
    state_deleted_id: str,
    state_tconfig_cache: tc.TableConfigParser.Cache,
) -> Tuple[types.Table, int, str, dbc.Toast, str, str, bool, int]:
    """Exterior control signaled that the table should be updated.

    This is either a filter, "add new", refresh, or "show totals". Only
    "add new" changes MoU DS data. The others simply change what's
    visible to the user.
    """
    logging.warning(f"'{du.triggered_id()}' -> table_data_exterior_controls()")

    # Dash sets cleared values as 0
    # TODO - move this to DS.py and fix types to reflect it can be None/0/etc.
    # state_snapshot_ts = state_snapshot_ts if state_snapshot_ts else ""
    # labor = labor if labor else ""
    # institution = institution if institution else ""

    logging.warning(
        f"Snapshot: {state_snapshot_ts=} {'' if state_snapshot_ts else '(Live Collection)'}"
    )

    table: types.Table = []
    toast: dbc.Toast = None

    # format "Show Totals" button
    show_totals, tot_label, tot_color, tot_outline, all_cols = _totals_button_logic(
        tot_n_clicks, state_all_cols
    )

    # Add New Data
    if re.match(r"wbs-new-data-button-\d+", du.triggered_id()):
        if not state_snapshot_ts:  # are we looking at a snapshot?
            table, toast = _add_new_data(
                wbs_l1,
                state_table,
                state_columns,
                labor,
                institution,
                state_tconfig_cache,
            )

    # OR Restore a types.Record and Pull types.Table (optionally filtered)
    elif du.triggered_id() == "wbs-undo-last-delete":
        if not state_snapshot_ts:  # are we looking at a snapshot?
            try:
                table = src.pull_data_table(
                    wbs_l1,
                    institution=institution,
                    labor=labor,
                    with_totals=show_totals,
                    restore_id=state_deleted_id,
                )
                toast = du.make_toast(
                    "types.Record Restored",
                    f"id: {state_deleted_id}",
                    du.Color.SUCCESS,
                    5,
                )
            except DataSourceException:
                table = []

    # OR Just Pull types.Table (optionally filtered)
    else:
        try:
            table = src.pull_data_table(
                wbs_l1,
                institution=institution,
                labor=labor,
                with_totals=show_totals,
                snapshot_ts=state_snapshot_ts,
            )
        except DataSourceException:
            table = []

    return (
        table,
        0,  # go to first page
        du.get_now(),  # record now
        toast,
        tot_label,
        tot_color,
        tot_outline,
        all_cols,
    )


def _push_modified_records(
    wbs_l1: str,
    current_table: types.Table,
    previous_table: types.Table,
    state_tconfig_cache: tc.TableConfigParser.Cache,
) -> List[types.StrNum]:
    """For each row that changed, push the record to the DS."""
    modified_records = [
        r for r in current_table if (r not in previous_table) and (src.ID in r)
    ]
    for record in modified_records:
        try:
            src.push_record(wbs_l1, record, tconfig_cache=state_tconfig_cache)
        except DataSourceException:
            pass

    ids = [c[src.ID] for c in modified_records]
    return ids


def _delete_deleted_records(
    wbs_l1: str,
    current_table: types.Table,
    previous_table: types.Table,
    keeps: List[types.StrNum],
) -> Tuple[dbc.Toast, str]:
    """For each row that was deleted by the user, delete its DS record."""
    toast: dbc.Toast = None
    last_deletion = ""

    delete_these = [
        r
        for r in previous_table
        if (r not in current_table) and (src.ID in r) and (r[src.ID] not in keeps)
    ]

    failures = []
    record = None
    for record in delete_these:
        try:
            src.delete_record(wbs_l1, cast(str, record[src.ID]))
            last_deletion = cast(str, record[src.ID])
        except DataSourceException:
            failures.append(record)

    # make toast message if any records failed to be deleted
    if failures:
        toast = du.make_toast(
            f"Failed to Delete types.Record {record[src.ID]}",
            du.REFRESH_MSG,
            du.Color.DANGER,
        )

    return toast, last_deletion


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-data-table", "data_previous"),
        Output("wbs-toast-via-interior-control-div", "children"),
        Output("wbs-table-last-updated-label", "children"),
        Output("wbs-last-deleted-id", "children"),
        Output("wbs-deletion-toast", "is_open"),
    ],
    [Input("wbs-data-table", "data")],
    [
        State("wbs-current-l1", "value"),
        State("wbs-data-table", "data_previous"),
        State("wbs-table-exterior-control-last-timestamp", "data"),
        State("wbs-table-config-cache", "data"),
        State("wbs-current-snapshot-ts", "value"),
    ],
    prevent_initial_call=True,
)
def table_data_interior_controls(
    # other input(s)
    current_table: types.Table,
    # L1 value (state)
    wbs_l1: str,
    # state(s)
    previous_table: types.Table,
    table_exterior_control_ts: str,
    state_tconfig_cache: tc.TableConfigParser.Cache,
    state_snap_current_ts: types.DDValue,
) -> Tuple[types.Table, dbc.Toast, str, str, bool]:
    """Interior control signaled that the table should be updated.

    This is either a row deletion or a field edit. The table's view has
    already been updated, so only DS communication is needed.

    NOTE: This function is also called following table_data_exterior_controls().
    This is unnecessary, so the timestamp of table_data_exterior_controls()'s
    last call will be checked to determine if that was indeed the case.
    """
    logging.warning(f"'{du.triggered_id()}' -> table_data_interior_controls()")

    updated_message = f"Table Last Refreshed: {du.get_human_now()}"

    # IF This is a snapshot
    # OR no previous table -- probably unlikely
    # OR table was just updated via exterior controls
    if (
        state_snap_current_ts
        or (not previous_table)
        or du.was_recent(table_exterior_control_ts)
    ):
        return current_table, None, updated_message, "", False

    # Push (if any)
    mod_ids = _push_modified_records(
        wbs_l1, current_table, previous_table, state_tconfig_cache
    )

    # Delete (if any)
    toast, last_deletion = _delete_deleted_records(
        wbs_l1, current_table, previous_table, mod_ids
    )

    # Update data_previous
    return current_table, toast, updated_message, last_deletion, bool(last_deletion)


@app.callback(  # type: ignore[misc]
    Output("wbs-data-table", "columns"),
    [Input("wbs-data-table", "editable")],
    [State("wbs-table-config-cache", "data")],
    prevent_initial_call=True,
)
def table_columns_callback(
    # input(s)
    table_editable: bool,
    # state(s)
    state_tconfig_cache: tc.TableConfigParser.Cache,
) -> List[Dict[str, object]]:
    """Grab table columns, toggle whether a column is editable."""
    logging.warning(f"'{du.triggered_id()}' -> table_columns()")

    tconfig = tc.TableConfigParser(state_tconfig_cache)

    # disable institution, unless user is an admin
    # follows order of precedence for editable-ness: table > column > disable_institution
    is_institution_editable = False
    if current_user.is_authenticated and current_user.is_admin:
        is_institution_editable = True

    return du.table_columns(
        tconfig,
        table_editable=table_editable,
        is_institution_editable=is_institution_editable,
    )


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-data-table", "dropdown"),
        Output("wbs-data-table", "dropdown_conditional"),
    ],
    [Input("wbs-data-table", "editable")],
    [State("wbs-table-config-cache", "data")],
)
def table_dropdown(
    # input(s)
    _: bool,
    # state(s)
    state_tconfig_cache: tc.TableConfigParser.Cache,
) -> Tuple[types.TDDown, types.TDDownCond]:
    """Grab table dropdowns."""
    logging.warning(f"'{du.triggered_id()}' -> table_dropdown()")

    simple_dropdowns: types.TDDown = {}
    conditional_dropdowns: types.TDDownCond = []
    tconfig = tc.TableConfigParser(state_tconfig_cache)

    def _options(menu: List[str]) -> List[Dict[str, str]]:
        return [{"label": m, "value": m} for m in menu]

    for col in tconfig.get_dropdown_columns():
        # Add simple dropdowns
        if tconfig.is_simple_dropdown(col):
            dropdown = tconfig.get_simple_column_dropdown_menu(col)
            simple_dropdowns[col] = {"options": _options(dropdown)}

        # Add conditional dropdowns
        elif tconfig.is_conditional_dropdown(col):
            # get parent column and its options
            (
                parent_col,
                parent_col_opts,
            ) = tconfig.get_conditional_column_parent_and_options(col)
            # make filter_query for each parent-column option
            for parent_opt in parent_col_opts:
                dropdown = tconfig.get_conditional_column_dropdown_menu(col, parent_opt)
                conditional_dropdowns.append(
                    {
                        "if": {
                            "column_id": col,
                            "filter_query": f'''{{{parent_col}}} eq "{parent_opt}"''',
                        },
                        "options": _options(dropdown),
                    }
                )

        # Error
        else:
            raise Exception(f"Dropdown column ({col}) is not simple nor conditional.")

    return simple_dropdowns, conditional_dropdowns


# --------------------------------------------------------------------------------------
# Snapshot Callbacks


@app.callback(  # type: ignore[misc]
    Output("wbs-current-snapshot-ts", "value"),
    [Input("wbs-view-live-btn", "n_clicks")],
    prevent_initial_call=True,
)
def view_live_table(_: int) -> types.DDValue:
    """Clear the snapshot selection."""
    logging.warning(f"'{du.triggered_id()}' -> view_live_table()")
    return ""


@app.callback(  # type: ignore[misc]
    Output("refresh-for-snapshot-change", "run"),
    [Input("wbs-current-snapshot-ts", "value")],
    prevent_initial_call=True,
)
def pick_snapshot(_: types.DDValue) -> str:
    """Refresh the page on snapshot select/de-select."""
    logging.warning(f"'{du.triggered_id()}' -> pick_snapshot()")
    return "location.reload();"


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-current-snapshot-ts", "options"),
        Output("wbs-snapshot-current-labels", "children"),
        Output("wbs-viewing-snapshot-alert", "is_open"),
    ],
    [Input("dummy-input-for-setup", "hidden")],
    [State("wbs-current-l1", "value"), State("wbs-current-snapshot-ts", "value")],
)
def setup_snapshot_components(
    _: bool,
    # state(s)
    wbs_l1: str,
    snap_ts: types.DDValue,
) -> Tuple[List[Dict[str, str]], List[html.Label], bool]:
    """Set up snapshot-related components."""
    logging.warning(
        f"'{du.triggered_id()}' -> setup_snapshot_components()  ({wbs_l1=} {snap_ts=})"
    )

    assert not du.triggered_id()  # Guarantee this is the initial call

    snap_options: List[Dict[str, str]] = []
    label_lines: List[html.Label] = []
    snapshots: List[types.SnapshotInfo] = []

    # Populate List of Snapshots
    try:
        snapshots = src.list_snapshots(wbs_l1)
    except DataSourceException:
        pass
    snap_options = [
        {
            "label": f"{snap['name']}  [created by {snap['creator']} on {du.get_human_time(snap['timestamp'])}]",
            "value": snap["timestamp"],
        }
        for snap in snapshots
    ]

    # This was a tab switch w/ a now non-valid snap ts
    if snap_ts not in [snap["timestamp"] for snap in snapshots]:
        snap_ts = ""

    # Selected a Snapshot
    if snap_ts:
        snap_info = next(s for s in snapshots if s["timestamp"] == snap_ts)
        human_time = du.get_human_time(snap_info["timestamp"])
        # get lines
        label_lines = [
            html.Label(f"\"{snap_info['name']}\""),
            html.Label(
                f"(created by {snap_info['creator']} — {human_time})",
                style={"font-size": "75%", "font-style": "italic"},
            ),
        ]

    return snap_options, label_lines, bool(snap_ts)


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-name-snapshot", "is_open"),
        Output("wbs-toast-via-snapshot-div", "children"),
        Output("wbs-make-snapshot-button", "color"),  # triggers "Loading" element
    ],
    [
        Input("wbs-make-snapshot-button", "n_clicks"),
        Input("wbs-name-snapshot-btn", "n_clicks"),
        Input("wbs-name-snapshot-input", "n_submit"),
    ],
    [
        State("wbs-l1", "value"),
        State("wbs-name-snapshot-input", "value"),
        State("wbs-snapshot-current-ts", "value"),
    ],
    prevent_initial_call=True,
)
def handle_make_snapshot(
    # input(s)
    _: int,
    __: int,
    ___: int,
    # L1 value (state)
    wbs_l1: str,
    # other state(s)
    name: str,
    state_snap_current_ts: str,
) -> Tuple[bool, dbc.Toast, str]:
    """Handle the naming and creating of a snapshot."""
    logging.warning(f"'{du.triggered_id()}' -> handle_make_snapshot()")

    if state_snap_current_ts:  # are we looking at a snapshot?
        return False, None, ""

    if du.triggered_id() == "wbs-make-snapshot-button":
        return True, None, ""

    if du.triggered_id() in ["wbs-name-snapshot-btn", "wbs-name-snapshot-input"]:
        try:
            snapshot = src.create_snapshot(wbs_l1, name)
            message = [
                f"Name: {snapshot['name']}",
                f"Timestamp: {du.get_human_time(snapshot['timestamp'])}",
                f"Creator: {snapshot['creator']}",
            ]
            return (
                False,
                du.make_toast("Snapshot Created", message, du.Color.SUCCESS, 5),
                du.Color.SUCCESS,
            )
        except DataSourceException:
            return (
                False,
                du.make_toast(
                    "Failed to Make Snapshot", du.REFRESH_MSG, du.Color.DANGER
                ),
                du.Color.SUCCESS,
            )

    raise Exception(f"Unaccounted trigger {du.triggered_id()}")


# --------------------------------------------------------------------------------------
# Institution Callbacks


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-phds-authors", "value"),
        Output("wbs-faculty", "value"),
        Output("wbs-scientists-post-docs", "value"),
        Output("wbs-grad-students", "value"),
        Output("wbs-textarea", "value"),
        Output("wbs-h2-sow-table", "children"),
        Output("wbs-h2-inst-textarea", "children"),
        Output("institution-headcounts-container", "hidden"),
        Output("institution-textarea-container", "hidden"),
        Output("wbs-current-institution", "value"),
    ],
    [Input("dummy-input-for-setup", "hidden")],
    [
        State("wbs-current-l1", "value"),
        State("wbs-current-snapshot-ts", "value"),
        State("wbs-current-institution", "value"),
    ],
)
def setup_institution_components(
    _: bool,
    # state(s)
    wbs_l1: str,
    snap_ts: types.DDValue,
    institution: types.DDValue,
) -> Tuple[int, int, int, int, str, str, str, bool, bool, types.DDValue]:
    """Set up institution-related components."""
    logging.warning(
        f"'{du.triggered_id()}' -> setup_institution_components() ({wbs_l1=} {snap_ts=} {institution=})"
    )

    assert not du.triggered_id()  # Guarantee this is the initial call

    h2_sow_table = "Collaboration-Wide SOW Table"

    # auto-select institution if the user is a non-admin
    if current_user.is_authenticated and not current_user.is_admin:
        institution = current_user.institution

    if not institution:
        return 0, 0, 0, 0, "", h2_sow_table, "", True, True, institution

    h2_sow_table = f"{institution}'s SOW Table"
    h2_notes = f"{institution}'s Notes and Descriptions"

    try:
        values = src.pull_institution_values(wbs_l1, snap_ts, institution)
        return (
            values["phds_authors"],
            values["faculty"],
            values["scientists_post_docs"],
            values["grad_students"],
            values["text"],
            h2_sow_table,
            h2_notes,
            False,
            False,
            institution,
        )

    except DataSourceException:
        return -1, -1, -1, -1, "", h2_sow_table, h2_notes, False, False, institution


@app.callback(  # type: ignore[misc]
    [
        Output("refresh-for-institution-change", "run"),
        Output("wbs-institution-dropdown-first-time-flag", "data"),
    ],
    [Input("wbs-current-institution", "value")],
    [State("wbs-institution-dropdown-first-time-flag", "data")],
    prevent_initial_call=True,
)
def pick_institution(institution: types.DDValue, first_time: bool) -> Tuple[str, bool]:
    """Refresh if the user selected an institution."""
    logging.warning(
        f"'{du.triggered_id()}' -> pick_institution() ({first_time=} {institution=})"
    )

    if first_time:
        return "", False

    return "location.reload();", False


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-institution-values-first-time-flag", "data"),
        Output("wbs-institution-values-last-updated-label", "children"),
        Output("wbs-institution-textarea-last-updated-label", "children"),
    ],
    [
        Input("wbs-phds-authors", "value"),
        Input("wbs-faculty", "value"),
        Input("wbs-scientists-post-docs", "value"),
        Input("wbs-grad-students", "value"),
        Input("wbs-textarea", "value"),
    ],
    [
        State("wbs-current-l1", "value"),
        State("wbs-current-institution", "value"),
        State("wbs-current-snapshot-ts", "value"),
        State("wbs-data-table", "data"),
        State("wbs-institution-values-first-time-flag", "data"),
    ],
    prevent_initial_call=True,
)
def push_institution_values(  # pylint: disable=R0913
    # input(s)
    phds_authors: int,
    faculty: int,
    scientists_post_docs: int,
    grad_students: int,
    text: str,
    # L1 value (state)
    wbs_l1: str,
    # other state(s)
    state_institution: types.DDValue,
    state_snap_current_ts: types.DDValue,
    state_table: types.Table,
    first_time: bool,
) -> Tuple[bool, html.Label, html.Label]:
    """Push the institution's values."""
    logging.warning(
        f"'{du.triggered_id()}' -> push_institution_values() ({first_time=})"
    )

    now = du.get_human_now()
    headcounts_label = html.Label(f"Headcounts Last Refreshed: {now}")
    textarea_label = html.Label(f"Notes & Descriptions Last Refreshed: {now}")

    if (
        not state_institution  # no institution selected
        or not current_user.is_authenticated
        or state_snap_current_ts  # are we looking at a snapshot?
        or first_time  # fields were just auto-populated for the first time
    ):
        return False, headcounts_label, textarea_label

    values: types.InstitutionValues = {
        "phds_authors": phds_authors,
        "faculty": faculty,
        "scientists_post_docs": scientists_post_docs,
        "grad_students": grad_students,
        "text": text,
    }

    try:
        src.push_institution_values(wbs_l1, state_institution, values)
    except DataSourceException:
        assert len(state_table) == 0  # there's no collection to push to

    return False, headcounts_label, textarea_label


# --------------------------------------------------------------------------------------
# Other Callbacks


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-data-table", "editable"),
        Output("wbs-new-data-div-1", "hidden"),
        Output("wbs-new-data-div-2", "hidden"),
        Output("wbs-data-table", "row_deletable"),
        Output("wbs-current-institution", "disabled"),
        Output("wbs-admin-zone-div", "hidden"),
        Output("wbs-phds-authors", "disabled"),
        Output("wbs-faculty", "disabled"),
        Output("wbs-scientists-post-docs", "disabled"),
        Output("wbs-grad-students", "disabled"),
        Output("wbs-textarea", "disabled"),
    ],
    [Input("dummy-input-for-setup", "hidden")],
    [State("wbs-current-snapshot-ts", "value")],
)
def setup_user_dependent_components(
    _: bool,
    # state(s)
    snap_ts: types.DDValue,
) -> Tuple[bool, bool, bool, bool, bool, bool, bool, bool, bool, bool, bool]:
    """Logged-in callback."""
    logging.warning(
        f"'{du.triggered_id()}' -> setup_user_dependent_components()  ({snap_ts=})"
    )

    assert not du.triggered_id()  # Guarantee this is the initial call

    if snap_ts:
        return (
            False,  # data-table NOT editable
            True,  # new-data-div-1 hidden
            True,  # new-data-div-2 hidden
            False,  # row NOT deletable
            False,  # filter-inst NOT disabled
            True,  # wbs-admin-zone-div hidden
            True,  # institution value disabled
            True,  # institution value disabled
            True,  # institution value disabled
            True,  # institution value disabled
            True,  # institution value disabled
        )

    if current_user.is_authenticated:
        return (
            True,  # data-table editable
            False,  # new-data-div-1 NOT hidden
            False,  # new-data-div-2 NOT hidden
            True,  # row is deletable
            not current_user.is_admin,  # filter-inst disabled if user is not an admin
            not current_user.is_admin,  # wbs-admin-zone-div hidden if user is not an admin
            False,  # institution value NOT disabled
            False,  # institution value NOT disabled
            False,  # institution value NOT disabled
            False,  # institution value NOT disabled
            False,  # institution value NOT disabled
        )
    return (
        False,  # data-table NOT editable
        True,  # new-data-div-1 hidden
        True,  # new-data-div-2 hidden
        False,  # row NOT deletable
        False,  # filter-inst NOT disabled
        True,  # wbs-admin-zone-div hidden
        True,  # institution value disabled
        True,  # institution value disabled
        True,  # institution value disabled
        True,  # institution value disabled
        True,  # institution value disabled
    )


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-show-all-rows-button", "children"),
        Output("wbs-show-all-rows-button", "color"),
        Output("wbs-show-all-rows-button", "outline"),
        Output("wbs-data-table", "page_size"),
        Output("wbs-data-table", "page_action"),
    ],
    [Input("wbs-show-all-rows-button", "n_clicks")],
    [State("wbs-table-config-cache", "data")],
)
def toggle_pagination(
    # input(s)
    n_clicks: int,
    # state(s)
    state_tconfig_cache: tc.TableConfigParser.Cache,
) -> Tuple[str, str, bool, int, str]:
    """Toggle whether the table is paginated."""
    logging.warning(f"'{du.triggered_id()}' -> toggle_pagination()")

    if n_clicks % 2 == 0:
        tconfig = tc.TableConfigParser(state_tconfig_cache)
        return (
            "Show All Rows",
            du.Color.SECONDARY,
            True,
            tconfig.get_page_size(),
            "native",
        )
    # https://community.plotly.com/t/rendering-all-rows-without-pages-in-datatable/15605/2
    return "Collapse Rows to Pages", du.Color.DARK, False, 9999999999, "none"


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-show-all-columns-button", "children"),
        Output("wbs-show-all-columns-button", "color"),
        Output("wbs-show-all-columns-button", "outline"),
        Output("wbs-data-table", "hidden_columns"),
    ],
    [Input("wbs-show-all-columns-button", "n_clicks")],
    [State("wbs-table-config-cache", "data")],
    prevent_initial_call=True,
)
def toggle_hidden_columns(
    # input(s)
    n_clicks: int,
    # state(s)
    state_tconfig_cache: tc.TableConfigParser.Cache,
) -> Tuple[str, str, bool, List[str]]:
    """Toggle hiding/showing the default hidden columns."""
    logging.warning(f"'{du.triggered_id()}' -> toggle_hidden_columns()")

    if n_clicks % 2 == 0:
        tconfig = tc.TableConfigParser(state_tconfig_cache)
        return (
            "Show Hidden Columns",
            du.Color.SECONDARY,
            True,
            tconfig.get_hidden_columns(),
        )
    return "Show Default Columns", du.Color.DARK, False, []
