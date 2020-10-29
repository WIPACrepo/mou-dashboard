"""Callbacks for a specified WBS layout."""

import logging
from typing import cast, Dict, List, Tuple

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_html_components as html  # type: ignore[import]
from dash import no_update  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]
from flask_login import current_user  # type: ignore[import]

from ..config import app
from ..data_source import data_source as src
from ..data_source import table_config as tc
from ..data_source.utils import DataSourceException
from ..utils import dash_utils as du
from ..utils import types

# --------------------------------------------------------------------------------------
# Table Callbacks


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
    labor: types.DashVal,
    institution: types.DashVal,
    state_tconfig_cache: tc.TableConfigParser.CacheType,
    state_new_task: str,
) -> Tuple[types.Table, dbc.Toast]:
    """Push new record to data source; add to table.

    Returns:
        TData     -- up-to-date data table
        dbc.Toast -- toast element with confirmation message
    """
    table = state_table
    column_names = [cast(str, c["name"]) for c in state_columns]
    new_record: types.Record = {n: "" for n in column_names}

    # push to data source AND auto-fill labor and/or institution
    try:
        new_record = src.push_record(
            wbs_l1,
            new_record,
            task=state_new_task,
            labor=labor,
            institution=institution,
            novel=True,
            tconfig=tc.TableConfigParser(wbs_l1, cache=state_tconfig_cache),
        )
        table.insert(0, new_record)
        message = [html.Div(s) for s in src.record_to_strings(new_record)]
        toast = du.make_toast("Record Added", message, du.Color.SUCCESS, 5)
    except DataSourceException:
        toast = du.make_toast("Failed to Make Record", du.REFRESH_MSG, du.Color.DANGER)

    return table, toast


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-new-data-modal", "is_open"),
        Output("wbs-new-data-modal-task", "value"),
        Output("wbs-new-data-modal-dummy-add", "n_clicks"),
        Output("wbs-new-data-modal-header", "children"),
    ],
    [
        Input("wbs-new-data-button-1", "n_clicks"),  # user-only
        Input("wbs-new-data-button-2", "n_clicks"),  # user-only
        Input("wbs-new-data-modal-add-button", "n_clicks"),  # user-only
    ],
    [
        State("wbs-new-data-modal-task", "value"),
        State("wbs-current-institution", "value"),
        State("wbs-filter-labor", "value"),
    ],
    prevent_initial_call=True,
)
def handle_add_new_data(
    # input(s)
    _: int,
    __: int,
    ___: int,
    # state(s)
    task: str,
    institution: str,
    labor: str,
) -> Tuple[bool, str, int, str]:
    """Handle the modal for adding a new row."""
    logging.warning(f"'{du.triggered_id()}' -> handle_add_new_data()")

    if du.triggered_id() == "wbs-new-data-modal-add-button":
        if not task:
            return no_update, no_update, no_update, no_update
        return False, task, 1, no_update

    header = "Add New Data"
    if institution:
        header += f" for {institution}"
    if labor:
        header += f" ({labor})"

    return True, "", no_update, header


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-data-table", "data"),
        Output("wbs-data-table", "page_current"),
        Output("wbs-toast-via-exterior-control-div", "children"),
        Output("wbs-show-totals-button", "children"),
        Output("wbs-show-totals-button", "color"),
        Output("wbs-show-totals-button", "outline"),
        Output("wbs-show-all-columns-button", "n_clicks"),
        Output("wbs-table-update-flag-exterior-control", "data"),
    ],
    [
        Input("wbs-data-table", "columns"),  # setup_table()-only
        Input("wbs-filter-labor", "value"),  # user/setup_institution_components()
        Input("wbs-show-totals-button", "n_clicks"),  # user-only
        Input("wbs-new-data-modal-dummy-add", "n_clicks"),  # handle_add_new_data()-only
        Input("wbs-undo-last-delete", "n_clicks"),  # user-only
    ],
    [
        State("wbs-current-l1", "value"),
        State("wbs-current-snapshot-ts", "value"),
        State("wbs-data-table", "data"),
        State("wbs-show-all-columns-button", "n_clicks"),
        State("wbs-last-deleted-id", "data"),
        State("wbs-table-config-cache", "data"),
        State("wbs-new-data-modal-task", "value"),
        State("wbs-current-institution", "value"),
        State("wbs-table-update-flag-exterior-control", "data"),
    ],
    prevent_initial_call=True,  # must wait for columns
)  # pylint: disable=R0913,R0914
def table_data_exterior_controls(
    # input(s)
    columns: types.TColumns,
    labor: types.DashVal,
    tot_n_clicks: int,
    _: int,
    __: int,
    # state(s)
    wbs_l1: str,
    state_snapshot_ts: types.DashVal,
    state_table: types.Table,
    state_all_cols: int,
    state_deleted_id: str,
    state_tconfig_cache: tc.TableConfigParser.CacheType,
    state_new_task: str,
    state_institution: types.DashVal,
    s_flag_extctrl: bool,
) -> Tuple[types.Table, int, dbc.Toast, str, str, bool, int, bool]:
    """Exterior control signaled that the table should be updated.

    This is either a filter, "add new", refresh, or "show totals". Only
    "add new" changes MoU DS data. The others simply change what's
    visible to the user.
    """
    logging.warning(f"'{du.triggered_id()}' -> table_data_exterior_controls()")
    logging.warning(
        f"Snapshot: {state_snapshot_ts=} {'' if state_snapshot_ts else '(Live Collection)'}"
    )

    assert columns

    table: types.Table = []
    toast: dbc.Toast = None

    # format "Show Totals" button
    show_totals, tot_label, tot_color, tot_outline, all_cols = _totals_button_logic(
        tot_n_clicks, state_all_cols
    )

    # Add New Data
    if du.triggered_id() == "wbs-new-data-modal-dummy-add":
        if not state_snapshot_ts:  # are we looking at a snapshot?
            table, toast = _add_new_data(
                wbs_l1,
                state_table,
                columns,
                labor,
                state_institution,
                state_tconfig_cache,
                state_new_task,
            )

    # OR Restore a types.Record and Pull types.Table (optionally filtered)
    elif du.triggered_id() == "wbs-undo-last-delete":
        if not state_snapshot_ts:  # are we looking at a snapshot?
            try:
                table = src.pull_data_table(
                    wbs_l1,
                    institution=state_institution,
                    labor=labor,
                    with_totals=show_totals,
                    restore_id=state_deleted_id,
                )
                record = next(r for r in table if r[src.ID] == state_deleted_id)
                message = [html.Div(s) for s in src.record_to_strings(record)]
                toast = du.make_toast("Record Restored", message, du.Color.SUCCESS, 5)
            except DataSourceException:
                table = []

    # OR Just Pull types.Table (optionally filtered)
    else:
        try:
            table = src.pull_data_table(
                wbs_l1,
                institution=state_institution,
                labor=labor,
                with_totals=show_totals,
                snapshot_ts=state_snapshot_ts,
            )
        except DataSourceException:
            table = []

    return (
        table,
        0,
        toast,
        tot_label,
        tot_color,
        tot_outline,
        all_cols,
        not s_flag_extctrl,  # toggle flag to send a message to table_interior_controls
    )


def _push_modified_records(
    wbs_l1: str,
    current_table: types.Table,
    previous_table: types.Table,
    tconfig: tc.TableConfigParser,
) -> List[types.StrNum]:
    """For each row that changed, push the record to the DS."""
    modified_records = [
        r for r in current_table if (r not in previous_table) and (src.ID in r)
    ]
    for record in modified_records:
        try:
            src.push_record(wbs_l1, record, tconfig=tconfig)
        except DataSourceException:
            pass

    ids = [c[src.ID] for c in modified_records]
    return ids


def _delete_deleted_records(
    wbs_l1: str,
    current_table: types.Table,
    previous_table: types.Table,
    keeps: List[types.StrNum],
) -> Tuple[dbc.Toast, str, List[str]]:
    """For each row that was deleted by the user, delete its DS record."""
    delete_these = [
        r
        for r in previous_table
        if (r not in current_table) and (src.ID in r) and (r[src.ID] not in keeps)
    ]

    if not delete_these:
        return None, "", []

    assert len(delete_these) == 1

    toast: dbc.Toast = None
    last_deletion = ""
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
            "Failed to Delete Record", du.REFRESH_MSG, du.Color.DANGER
        )
    else:
        success_message = [html.Div(s) for s in src.record_to_strings(delete_these[0])]

    return toast, last_deletion, success_message


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-data-table", "data_previous"),
        Output("wbs-toast-via-interior-control-div", "children"),
        Output("wbs-table-last-updated-label", "children"),
        Output("wbs-last-deleted-id", "data"),
        Output("wbs-deletion-toast", "is_open"),
        Output("wbs-deletion-toast-message", "children"),
        Output("wbs-table-update-flag-interior-control", "data"),
    ],
    [Input("wbs-data-table", "data")],  # user/table_data_exterior_controls()
    [
        State("wbs-current-l1", "value"),
        State("wbs-data-table", "data_previous"),
        State("wbs-table-config-cache", "data"),
        State("wbs-current-snapshot-ts", "value"),
        State("wbs-table-update-flag-exterior-control", "data"),
        State("wbs-table-update-flag-interior-control", "data"),
    ],
    prevent_initial_call=True,
)
def table_data_interior_controls(
    # input(s)
    current_table: types.Table,
    # state(s)
    wbs_l1: str,
    previous_table: types.Table,
    state_tconfig_cache: tc.TableConfigParser.CacheType,
    state_snap_current_ts: types.DashVal,
    s_flag_extctrl: bool,
    s_flag_intctrl: bool,
) -> Tuple[types.Table, dbc.Toast, str, str, bool, List[html.Div], bool]:
    """Interior control signaled that the table should be updated.

    This is either a row deletion or a field edit. The table's view has
    already been updated, so only DS communication is needed.

    NOTE: This function is also called following table_data_exterior_controls().
    So the flags are XOR'd to see whether to proceed.
    """
    logging.warning(f"'{du.triggered_id()}' -> table_data_interior_controls()")

    updated_message = f"Table Last Refreshed: {du.get_human_now()}"

    # Was table just updated via exterior controls? -- if so, toggle flag
    # flags will agree only after table_data_exterior_controls() triggers this function
    if not du.flags_agree(s_flag_extctrl, s_flag_intctrl):
        logging.warning("table_data_interior_controls() :: aborted callback")
        return current_table, None, updated_message, "", False, [], not s_flag_intctrl

    assert not state_snap_current_ts  # should not be a snapshot
    assert previous_table  # should have previous table

    # Push (if any)
    tconfig = tc.TableConfigParser(wbs_l1, cache=state_tconfig_cache)
    mod_ids = _push_modified_records(wbs_l1, current_table, previous_table, tconfig)

    # Delete (if any)
    toast, last_deletion, delete_success_message = _delete_deleted_records(
        wbs_l1, current_table, previous_table, mod_ids
    )

    # Update data_previous
    return (
        current_table,
        toast,
        updated_message,
        last_deletion,
        bool(last_deletion),
        delete_success_message,
        s_flag_intctrl,  # preserve flag
    )


def _table_columns_callback(
    table_editable: bool, tconfig: tc.TableConfigParser
) -> types.TColumns:
    """Grab table columns, toggle whether a column is editable.

    Disable institution, unless user is an admin. Follow order of
    precedence for editable-ness: table > column > disable_institution
    """
    is_institution_editable = False
    if current_user.is_authenticated and current_user.is_admin:
        is_institution_editable = True

    return du.table_columns(
        tconfig,
        table_editable=table_editable,
        is_institution_editable=is_institution_editable,
    )


def _table_dropdown(
    tconfig: tc.TableConfigParser,
) -> Tuple[types.TDDown, types.TDDownCond]:
    """Grab table dropdowns."""
    simple_dropdowns: types.TDDown = {}
    conditional_dropdowns: types.TDDownCond = []

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


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-data-table", "style_cell_conditional"),
        Output("wbs-data-table", "style_data_conditional"),
        Output("wbs-data-table", "tooltip"),
        Output("wbs-data-table", "columns"),
        Output("wbs-data-table", "dropdown"),
        Output("wbs-data-table", "dropdown_conditional"),
    ],
    [Input("wbs-data-table", "editable")],  # setup_user_dependent_components()-only
    [State("wbs-current-l1", "value"), State("wbs-table-config-cache", "data")],
    prevent_initial_call=True,
)
def setup_table(
    table_editable: bool,
    # state(s)
    wbs_l1: str,
    state_tconfig_cache: tc.TableConfigParser.CacheType,
) -> Tuple[
    types.TSCCond,
    types.TSDCond,
    types.TTooltips,
    types.TColumns,
    types.TDDown,
    types.TDDownCond,
]:
    """Set up table-related components."""
    logging.warning(f"'{du.triggered_id()}' -> setup_table()  ({wbs_l1=})")

    tconfig = tc.TableConfigParser(wbs_l1, cache=state_tconfig_cache)

    style_cell_conditional = du.style_cell_conditional(tconfig)
    style_data_conditional = du.get_style_data_conditional(tconfig)
    tooltip = du.get_table_tooltips(tconfig)
    columns = _table_columns_callback(table_editable, tconfig)
    simple_dropdowns, conditional_dropdowns = _table_dropdown(tconfig)

    return (
        style_cell_conditional,
        style_data_conditional,
        tooltip,
        columns,
        simple_dropdowns,
        conditional_dropdowns,
    )


# --------------------------------------------------------------------------------------
# Snapshot Callbacks


@app.callback(  # type: ignore[misc]
    Output("wbs-current-snapshot-ts", "value"),
    [Input("wbs-view-live-btn", "n_clicks")],  # user/pick_tab()
    prevent_initial_call=True,
)
def view_live_table(_: int) -> types.DashVal:
    """Clear the snapshot selection."""
    logging.warning(f"'{du.triggered_id()}' -> view_live_table()")
    return ""


@app.callback(  # type: ignore[misc]
    Output("refresh-for-snapshot-change", "run"),
    [Input("wbs-current-snapshot-ts", "value")],  # user/view_live_table()
    prevent_initial_call=True,
)
def pick_snapshot(_: types.DashVal) -> str:
    """Refresh the page on snapshot select/de-select."""
    logging.warning(f"'{du.triggered_id()}' -> pick_snapshot()")
    return "location.reload();"


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-current-snapshot-ts", "options"),
        Output("wbs-snapshot-current-labels", "children"),
        Output("wbs-viewing-snapshot-alert", "is_open"),
    ],
    [Input("dummy-input-for-setup", "hidden")],  # never triggered
    [State("wbs-current-l1", "value"), State("wbs-current-snapshot-ts", "value")],
)
def setup_snapshot_components(
    _: bool,
    # state(s)
    wbs_l1: str,
    snap_ts: types.DashVal,
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
        Output("refresh-for-snapshot-make", "run"),
    ],
    [
        Input("wbs-make-snapshot-button", "n_clicks"),  # user-only
        Input("wbs-name-snapshot-btn", "n_clicks"),  # user-only
        Input("wbs-name-snapshot-input", "n_submit"),  # user-only
    ],
    [
        State("wbs-current-l1", "value"),
        State("wbs-name-snapshot-input", "value"),
        State("wbs-current-snapshot-ts", "value"),
    ],
    prevent_initial_call=True,
)
def handle_make_snapshot(
    # input(s)
    _: int,
    __: int,
    ___: int,
    # state(s)
    wbs_l1: str,
    name: str,
    state_snap_current_ts: str,
) -> Tuple[bool, dbc.Toast, str, str]:
    """Handle the naming and creating of a snapshot."""
    logging.warning(f"'{du.triggered_id()}' -> handle_make_snapshot()")

    if state_snap_current_ts:  # are we looking at a snapshot?
        return False, None, "", ""

    if du.triggered_id() == "wbs-make-snapshot-button":
        return True, None, "", ""

    if du.triggered_id() in ["wbs-name-snapshot-btn", "wbs-name-snapshot-input"]:
        try:
            src.create_snapshot(wbs_l1, name)
            return False, "", "", "location.reload();"
        except DataSourceException:
            fail_toast = du.make_toast(
                "Failed to Make Snapshot", du.REFRESH_MSG, du.Color.DANGER
            )
            return False, fail_toast, du.Color.SUCCESS, ""

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
        Output("wbs-current-institution", "options"),
        Output("wbs-filter-labor", "options"),
    ],
    [Input("dummy-input-for-setup", "hidden")],  # never triggered
    [
        State("wbs-current-l1", "value"),
        State("wbs-current-snapshot-ts", "value"),
        State("wbs-current-institution", "value"),
        State("wbs-table-config-cache", "data"),
    ],
)
def setup_institution_components(
    _: bool,
    # state(s)
    wbs_l1: str,
    snap_ts: types.DashVal,
    institution: types.DashVal,
    state_tconfig_cache: tc.TableConfigParser.CacheType,
) -> Tuple[
    types.DashVal,
    types.DashVal,
    types.DashVal,
    types.DashVal,
    str,
    str,
    str,
    bool,
    bool,
    types.DashVal,
    List[Dict[str, str]],
    List[Dict[str, str]],
]:
    """Set up institution-related components."""
    logging.warning(
        f"'{du.triggered_id()}' -> setup_institution_components() ({wbs_l1=} {snap_ts=} {institution=})"
    )

    assert not du.triggered_id()  # Guarantee this is the initial call

    h2_sow_table = "Collaboration-Wide SOW Table"

    # auto-select institution if the user is a non-admin
    if current_user.is_authenticated and not current_user.is_admin:
        institution = current_user.institution

    tconfig = tc.TableConfigParser(wbs_l1, cache=state_tconfig_cache)
    inst_options = [
        {"label": f"{abbrev} ({name})", "value": abbrev}
        for name, abbrev in tconfig.get_institutions_w_abbrevs()
    ]
    lab_options = [{"label": st, "value": st} for st in tconfig.get_labor_categories()]

    if not institution:
        return (
            0,
            0,
            0,
            0,
            "",
            h2_sow_table,
            "",
            True,
            True,
            institution,
            inst_options,
            lab_options,
        )

    h2_table = f"{institution}'s SOW Table"
    h2_notes = f"{institution}'s Notes and Descriptions"

    phds: types.DashVal = None
    faculty: types.DashVal = None
    sci: types.DashVal = None
    grad: types.DashVal = None
    text: str = ""

    try:
        phds, faculty, sci, grad, text = src.pull_institution_values(
            wbs_l1, snap_ts, institution
        )
    except DataSourceException:
        pass

    return (
        phds,
        faculty,
        sci,
        grad,
        text,
        h2_table,
        h2_notes,
        False,
        False,
        institution,
        inst_options,
        lab_options,
    )


@app.callback(  # type: ignore[misc]
    [
        Output("refresh-for-institution-change", "run"),
        Output("wbs-institution-dropdown-first-time-flag", "data"),
    ],
    [Input("wbs-current-institution", "value")],  # user/setup_institution_components()
    [State("wbs-institution-dropdown-first-time-flag", "data")],
    prevent_initial_call=True,
)
def pick_institution(institution: types.DashVal, first_time: bool) -> Tuple[str, bool]:
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
        Input("wbs-phds-authors", "value"),  # user/setup_institution_components()
        Input("wbs-faculty", "value"),  # user/setup_institution_components()
        Input("wbs-scientists-post-docs", "value"),  # user/setup_institution_components
        Input("wbs-grad-students", "value"),  # user/setup_institution_components()
        Input("wbs-textarea", "value"),  # user/setup_institution_components()
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
    phds: types.DashVal,
    faculty: types.DashVal,
    sci: types.DashVal,
    grad: types.DashVal,
    text: str,
    # state(s)
    wbs_l1: str,
    institution: types.DashVal,
    state_snap_current_ts: types.DashVal,
    state_table: types.Table,
    first_time: bool,
) -> Tuple[bool, html.Label, html.Label]:
    """Push the institution's values."""
    logging.warning(
        f"'{du.triggered_id()}' -> push_institution_values() ({first_time=})"
    )

    # Is there an institution selected?
    if not institution:
        return False, None, None

    # labels
    now = du.get_human_now()
    textarea_label = html.Label(f"Notes & Descriptions Last Refreshed: {now}")
    headcounts_label = html.Label(f"Headcounts Last Refreshed: {now}")

    # Are the fields editable?
    if not current_user.is_authenticated and not state_snap_current_ts:
        return False, headcounts_label, textarea_label

    # check if headcounts are filled out
    if None in [phds, faculty, sci, grad]:
        headcounts_label = html.Label(
            "Headcounts are required. Please enter all four numbers.",
            style={"color": "red", "font-weight": "bold"},
        )

    # Is this a redundant push? -- fields were just auto-populated for the first time
    if first_time:
        return False, headcounts_label, textarea_label

    # push
    try:
        src.push_institution_values(wbs_l1, institution, phds, faculty, sci, grad, text)
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
    [Input("dummy-input-for-setup", "hidden")],  # never triggered
    [State("wbs-current-snapshot-ts", "value")],
)
def setup_user_dependent_components(
    _: bool,
    # state(s)
    snap_ts: types.DashVal,
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
    [Input("wbs-show-all-rows-button", "n_clicks")],  # user-only
    [State("wbs-table-config-cache", "data"), State("wbs-current-l1", "value")],
)
def toggle_pagination(
    # input(s)
    n_clicks: int,
    # state(s)
    state_tconfig_cache: tc.TableConfigParser.CacheType,
    wbs_l1: str,
) -> Tuple[str, str, bool, int, str]:
    """Toggle whether the table is paginated."""
    logging.warning(f"'{du.triggered_id()}' -> toggle_pagination()")

    if n_clicks % 2 == 0:
        tconfig = tc.TableConfigParser(wbs_l1, cache=state_tconfig_cache)
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
    [Input("wbs-show-all-columns-button", "n_clicks")],  # user/table_data_exterior_c...
    [State("wbs-table-config-cache", "data"), State("wbs-current-l1", "value")],
    prevent_initial_call=True,
)
def toggle_hidden_columns(
    # input(s)
    n_clicks: int,
    # state(s)
    state_tconfig_cache: tc.TableConfigParser.CacheType,
    wbs_l1: str,
) -> Tuple[str, str, bool, List[str]]:
    """Toggle hiding/showing the default hidden columns."""
    logging.warning(f"'{du.triggered_id()}' -> toggle_hidden_columns()")

    tconfig = tc.TableConfigParser(wbs_l1, cache=state_tconfig_cache)

    if n_clicks % 2 == 0:
        return (
            "Show Hidden Columns",
            du.Color.SECONDARY,
            True,
            tconfig.get_hidden_columns(),
        )

    always_hidden_columns = tconfig.get_always_hidden_columns()
    return "Show Default Columns", du.Color.DARK, False, always_hidden_columns