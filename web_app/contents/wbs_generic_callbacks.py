"""Callbacks for a specified WBS layout."""

import logging
from typing import Dict, List, Tuple, cast

import dash_bootstrap_components as dbc  # type: ignore[import]
import universal_utils.types as uut
from dash import html, no_update  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]

from ..config import app
from ..data_source import data_source as src
from ..data_source import institution_info
from ..data_source import table_config as tc
from ..data_source.utils import DataSourceException
from ..utils import dash_utils as du
from ..utils import types, utils
from ..utils.oidc_tools import CurrentUser

# --------------------------------------------------------------------------------------
# Table Callbacks


def _totals_button_logic(
    n_clicks: int, all_cols: int
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
        return False, "Show Totals", du.Color.SECONDARY, True, all_cols

    if triggered:  # on and triggered -> trigger "show-all-columns"
        return True, "Hide Totals", du.Color.DARK, False, 1

    # on and not triggered, AKA already on -> don't trigger "show-all-columns"
    return True, "Hide Totals", du.Color.DARK, False, all_cols


def _add_new_data(  # pylint: disable=R0913
    wbs_l1: str,
    table: uut.WebTable,
    columns: types.TColumns,
    labor: types.DashVal,
    institution: types.DashVal,
    tconfig: tc.TableConfigParser,
) -> Tuple[uut.WebTable, dbc.Toast]:
    """Push new record to data source; add to table.

    Returns:
        TData     -- up-to-date data table
        dbc.Toast -- toast element with confirmation message
    """
    new_record: uut.WebRecord = {
        nam: "" for nam in [cast(str, col["name"]) for col in columns]
    }

    # push to data source AND auto-fill labor and/or institution
    try:
        new_record = src.push_record(
            wbs_l1,
            new_record,
            tconfig,
            labor=labor,
            institution=institution,
            novel=True,
        )
        table.insert(0, new_record)
        toast = du.make_toast("Row Added", [], du.Color.SUCCESS, du.GOOD_WAIT)
    except DataSourceException:
        toast = du.make_toast("Failed to Add Row", du.REFRESH_MSG, du.Color.DANGER)

    return table, toast


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-toast-via-confirm-deletion-div", "children"),
        Output("wbs-undo-last-delete-hidden-button", "n_clicks"),
        Output("wbs-after-deletion-toast", "is_open"),
        Output("wbs-after-deletion-toast-message", "children"),
    ],
    [
        Input("wbs-confirm-deletion", "submit_n_clicks"),  # user-only
        Input("wbs-confirm-deletion", "cancel_n_clicks"),  # user-only
    ],
    [
        State("url", "pathname"),
        State("wbs-last-deleted-record", "data"),
    ],
    prevent_initial_call=True,
)
def confirm_deletion(
    _: int,
    __: int,
    # state(s)
    s_urlpath: str,
    s_record: uut.WebRecord,
) -> Tuple[dbc.Toast, int, bool, List[html.Div]]:
    """Handle deleting the record chosen ."""
    logging.warning(f"'{du.triggered()}' -> confirm_deletion()")

    # Don't delete record
    if du.triggered_property() == "cancel_n_clicks":
        return None, 1, no_update, []

    # Delete record
    elif du.triggered_property() == "submit_n_clicks":
        try:
            wbs_l1 = du.get_wbs_l1(s_urlpath)
            tconfig = tc.TableConfigParser(wbs_l1)
            src.delete_record(wbs_l1, cast(str, s_record[tconfig.const.ID]))
            lines = [html.Div(s) for s in src.record_to_strings(s_record, tconfig)]
            return None, no_update, True, lines
        except DataSourceException:
            msg = "Failed to Delete Row"
            toast = du.make_toast(msg, du.REFRESH_MSG, du.Color.DANGER)
            return toast, no_update, False, []

    else:
        raise Exception(f"Unaccounted for trigger {du.triggered()}")


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
        Output("wbs-show-all-rows-button", "n_clicks"),
        Output("wbs-show-all-rows-button", "style"),
    ],
    [
        Input("wbs-data-table", "columns"),  # setup_table()-only
        Input("wbs-filter-labor", "value"),  # user
        Input("wbs-show-totals-button", "n_clicks"),  # user-only
        Input("wbs-new-data-button-1", "n_clicks"),  # user-only
        Input("wbs-new-data-button-2", "n_clicks"),  # user-only
        Input("wbs-undo-last-delete-hidden-button", "n_clicks"),  # confirm_deletion()
    ],
    [
        State("url", "pathname"),
        State("wbs-current-snapshot-ts", "value"),
        State("wbs-data-table", "data"),
        State("wbs-show-all-columns-button", "n_clicks"),
        State("wbs-last-deleted-record", "data"),
        State("wbs-table-update-flag-exterior-control", "data"),
    ],
    prevent_initial_call=True,  # must wait for columns
)  # pylint: disable=R0913,R0914
def table_data_exterior_controls(
    columns: types.TColumns,
    labor: types.DashVal,
    tot_n_clicks: int,
    _: int,
    __: int,
    ___: int,
    # state(s)
    s_urlpath: str,
    s_snap_ts: types.DashVal,
    s_table: uut.WebTable,
    s_all_cols: int,
    s_deleted_record: uut.WebRecord,
    s_flag_extctrl: bool,
) -> Tuple[
    uut.WebTable, int, dbc.Toast, str, str, bool, int, bool, int, Dict[str, str]
]:
    """Exterior control signaled that the table should be updated.

    This is either a filter, "add new", refresh, or "show totals". Only
    "add new" changes MoU DS data. The others simply change what's
    visible to the user.
    """
    logging.warning(f"'{du.triggered()}' -> table_data_exterior_controls()")
    logging.warning(
        f"Snapshot: {s_snap_ts=} {'' if s_snap_ts else '(Live Collection)'}"
    )

    assert columns

    table: uut.WebTable = []
    toast: dbc.Toast = None
    wbs_l1 = du.get_wbs_l1(s_urlpath)
    inst = du.get_inst(s_urlpath)
    tconfig = tc.TableConfigParser(wbs_l1)

    # Format "Show Totals" button
    show_totals, tot_label, tot_color, tot_outline, all_cols = _totals_button_logic(
        tot_n_clicks, s_all_cols
    )

    # Add New Data
    if du.triggered_id() in ["wbs-new-data-button-1", "wbs-new-data-button-2"]:
        if not s_snap_ts:  # are we looking at a snapshot?
            table, toast = _add_new_data(
                wbs_l1,
                s_table,
                columns,
                labor,
                inst,
                tconfig,  # s_new_task
            )

    # OR Restore a uut.WebRecord and Pull uut.WebTable (optionally filtered)
    elif du.triggered_id() == "wbs-undo-last-delete-hidden-button":
        if not s_snap_ts:  # are we looking at a snapshot?
            try:
                table = src.pull_data_table(
                    wbs_l1,
                    tconfig,
                    institution=inst,
                    labor=labor,
                    with_totals=show_totals,
                    restore_id=cast(str, s_deleted_record[tconfig.const.ID]),
                )
                restored = next(
                    r
                    for r in table
                    if r[tconfig.const.ID] == s_deleted_record[tconfig.const.ID]
                )
                toast = du.make_toast(
                    "Row Restored",
                    [html.Div(s) for s in src.record_to_strings(restored, tconfig)],
                    du.Color.SUCCESS,
                    du.GOOD_WAIT,
                )
            except DataSourceException:
                table = []

    # OR Just Pull uut.WebTable (optionally filtered)
    else:
        try:
            table = src.pull_data_table(
                wbs_l1,
                tconfig,
                institution=inst,
                labor=labor,
                with_totals=show_totals,
                snapshot_ts=s_snap_ts,
            )
        except DataSourceException:
            table = []

    # Figure pagination
    do_paginate = (
        len(table) / tconfig.get_page_size() > 2  # paginate if 3+ pages
        and not inst  # paginate if viewing entire collaboration
        and CurrentUser.is_admin()  # paginate if admin
    )
    # hide "Show All Rows"/"Collapse Rows to Pages" if paginating wouldn't do anything
    style_paginate_button = {}
    if len(table) <= tconfig.get_page_size():
        style_paginate_button = {"visibility": "hidden"}

    return (
        table,
        0,
        toast,
        tot_label,
        tot_color,
        tot_outline,
        all_cols,
        not s_flag_extctrl,  # toggle flag to send a message to table_interior_controls
        int(not do_paginate),  # n_clicks: 0/even -> paginate; 1/odd -> don't paginate
        style_paginate_button,
    )


def _push_modified_records(
    wbs_l1: str,
    current_table: uut.WebTable,
    previous_table: uut.WebTable,
    tconfig: tc.TableConfigParser,
) -> Tuple[List[uut.StrNum], uut.WebRecord]:
    """For each row that changed, push the record to the DS."""
    modified_records = [
        r
        for r in current_table
        if (r not in previous_table) and (tconfig.const.ID in r)
    ]

    last_record = {}
    for record in modified_records:
        try:
            last_record = src.push_record(wbs_l1, record, tconfig)
        except DataSourceException:
            pass

    ids = [c[tconfig.const.ID] for c in modified_records]
    return ids, last_record


def _find_deleted_record(
    current_table: uut.WebTable,
    previous_table: uut.WebTable,
    keeps: List[uut.StrNum],
    tconfig: tc.TableConfigParser,
) -> Tuple[uut.WebRecord, str]:
    """If a row was deleted by the user, find it."""
    delete_these = [
        r
        for r in previous_table
        if (r not in current_table)
        and (tconfig.const.ID in r)
        and (r[tconfig.const.ID] not in keeps)
    ]

    if not delete_these:
        return {}, ""

    assert len(delete_these) == 1

    record = delete_these[0]
    record_fields = "\n".join(src.record_to_strings(record, tconfig))
    message = f"Are you sure you want to DELETE THIS ROW?\n\n{record_fields}"
    return record, message


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-data-table", "data_previous"),
        Output("wbs-table-timecheck-container", "children"),
        Output("wbs-last-deleted-record", "data"),
        Output("wbs-confirm-deletion", "displayed"),
        Output("wbs-confirm-deletion", "message"),
        Output("wbs-table-update-flag-interior-control", "data"),
        Output("wbs-sow-last-updated", "children"),
        Output("wbs-sow-last-updated-time", "children"),
    ],
    [Input("wbs-data-table", "data")],  # user/table_data_exterior_controls()
    [
        State("url", "pathname"),
        State("wbs-data-table", "data_previous"),
        State("wbs-current-snapshot-ts", "value"),
        State("wbs-table-update-flag-exterior-control", "data"),
        State("wbs-table-update-flag-interior-control", "data"),
    ],
    prevent_initial_call=True,
)  # pylint: disable=R0913,R0914
def table_data_interior_controls(
    current_table: uut.WebTable,
    # state(s)
    s_urlpath: str,
    s_previous_table: uut.WebTable,
    s_snap_ts: types.DashVal,
    s_flag_extctrl: bool,
    s_flag_intctrl: bool,
) -> Tuple[uut.WebTable, List[html.Label], uut.WebRecord, bool, str, bool, str, str]:
    """Interior control signaled that the table should be updated.

    This is either a row deletion or a field edit. The table's view has
    already been updated, so only DS communication is needed.

    NOTE: This function is also called following table_data_exterior_controls().
    So the flags are XOR'd to see whether to proceed.
    """
    logging.warning(f"'{du.triggered()}' -> table_data_interior_controls()")

    wbs_l1 = du.get_wbs_l1(s_urlpath)
    tconfig = tc.TableConfigParser(wbs_l1)

    # Make labels
    timecheck_labels = du.timecheck_labels("Table", "Autosaved", s_snap_ts)
    sows_updated_label = du.get_sow_last_updated_label(
        current_table, bool(s_snap_ts), tconfig
    )

    # Was table just updated via exterior controls? -- if so, toggle flag
    # flags will agree only after table_data_exterior_controls() triggers this function
    if not du.flags_agree(s_flag_extctrl, s_flag_intctrl):
        logging.warning("table_data_interior_controls() :: aborted callback")
        return (
            current_table,
            timecheck_labels,
            {},
            False,
            "",
            not s_flag_intctrl,
            "SOWs Last Updated:",
            sows_updated_label,
        )

    assert not s_snap_ts  # should not be a snapshot
    assert s_previous_table  # should have previous table

    # Push (if any)
    mod_ids, pushed_record = _push_modified_records(
        wbs_l1, current_table, s_previous_table, tconfig
    )

    # Delete (if any)
    deleted_record, delete_message = _find_deleted_record(
        current_table, s_previous_table, mod_ids, tconfig
    )

    # get the last updated label (make an ad hoc pseudo-table just to find the max time)
    if pushed_record or deleted_record:
        sows_updated_label = du.get_sow_last_updated_label(
            [pushed_record, deleted_record], bool(s_snap_ts), tconfig
        )

    # Update data_previous
    return (
        current_table,
        timecheck_labels,
        deleted_record,
        bool(deleted_record),
        delete_message,
        s_flag_intctrl,  # preserve flag
        "SOWs Last Updated:",
        sows_updated_label,
    )


def _table_columns_callback(
    table_editable: bool, tconfig: tc.TableConfigParser
) -> types.TColumns:
    """Grab table columns, toggle whether a column is editable.

    Disable institution, unless user is an admin. Follow order of
    precedence for editable-ness: table > column > disable_institution
    """
    is_institution_editable = False
    if CurrentUser.is_loggedin_with_permissions() and CurrentUser.is_admin():
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
    Output("wbs-data-table", "tooltip"),
    [Input("wbs-data-table", "page_current")],  # user and show_all_rows button
    [State("url", "pathname")],
    prevent_initial_call=True,
)
def load_table_tooltips(
    page_current: int | None,
    # state(s)
    s_urlpath: str,
) -> types.TTooltips:
    """Load the tooltips but only for the first page.

    This is a workaround for a bug in Dash source code where the tooltip
    is misplaced when on any page other than the first.
    """
    logging.warning(f"'{du.triggered()}' -> load_table_tooltips()  ({page_current=})")

    if page_current != 0:  # pages are 0-indexed
        return {}

    tconfig = tc.TableConfigParser(du.get_wbs_l1(s_urlpath))
    return du.get_table_tooltips(tconfig)


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-data-table", "style_cell_conditional"),
        Output("wbs-data-table", "style_data_conditional"),
        Output("wbs-data-table", "columns"),
        Output("wbs-data-table", "dropdown"),
        Output("wbs-data-table", "dropdown_conditional"),
    ],
    [Input("wbs-data-table", "editable")],  # setup_user_dependent_components()-only
    [State("url", "pathname")],
    prevent_initial_call=True,
)
def setup_table(
    table_editable: bool,
    # state(s)
    s_urlpath: str,
) -> Tuple[
    types.TSCCond,
    types.TSDCond,
    types.TColumns,
    types.TDDown,
    types.TDDownCond,
]:
    """Set up table-related components."""
    logging.warning(f"'{du.triggered()}' -> setup_table()  ({s_urlpath=})")

    tconfig = tc.TableConfigParser(du.get_wbs_l1(s_urlpath))

    style_cell_conditional = du.style_cell_conditional(tconfig)
    style_data_conditional = du.get_style_data_conditional(tconfig)
    columns = _table_columns_callback(table_editable, tconfig)
    simple_dropdowns, conditional_dropdowns = _table_dropdown(tconfig)

    return (
        style_cell_conditional,
        style_data_conditional,
        columns,
        simple_dropdowns,
        conditional_dropdowns,
    )


# --------------------------------------------------------------------------------------
# Snapshot Callbacks


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-snapshot-dropdown-div", "hidden"),
        Output("wbs-view-snapshots", "hidden"),
        Output("wbs-view-live-btn-div", "hidden"),
    ],
    [Input("wbs-view-snapshots", "n_clicks")],  # user
    [State("wbs-current-snapshot-ts", "value")],
)
def show_snapshot_dropdown(_: int, s_snap_ts: types.DashVal) -> Tuple[bool, bool, bool]:
    """Unhide the snapshot dropdown."""
    if s_snap_ts:  # show "View Live"
        return True, True, False

    if du.triggered_id() == "wbs-view-snapshots":  # show dropdown
        return False, True, True

    return True, False, True  # show "View Snapshots"


@app.callback(  # type: ignore[misc]
    Output("wbs-current-snapshot-ts", "value"),  # update to call pick_snapshot()
    [Input("wbs-view-live-btn", "n_clicks")],  # user/pick_tab()
    prevent_initial_call=True,
)
def view_live_table(_: int) -> types.DashVal:
    """Clear the snapshot selection."""
    logging.warning(f"'{du.triggered()}' -> view_live_table()")
    return ""


@app.callback(  # type: ignore[misc]
    Output("refresh-for-snapshot-change", "run"),
    [Input("wbs-current-snapshot-ts", "value")],  # user/view_live_table()
    prevent_initial_call=True,
)
def pick_snapshot(snap_ts: types.DashVal) -> str:
    """Refresh the page on snapshot select/de-select."""
    logging.warning(f"'{du.triggered()}' -> pick_snapshot() {snap_ts=}")
    return du.RELOAD


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-current-snapshot-ts", "options"),
        Output("wbs-snapshot-current-labels", "children"),
        Output("wbs-viewing-snapshot-alert", "is_open"),
    ],
    [Input("dummy-input-for-setup", "hidden")],  # never triggered
    [State("url", "pathname"), State("wbs-current-snapshot-ts", "value")],
)
def setup_snapshot_components(
    _: bool,
    # state(s)
    s_urlpath: str,
    s_snap_ts: types.DashVal,
) -> Tuple[List[Dict[str, str]], List[html.Label], bool]:
    """Set up snapshot-related components."""
    try:
        du.precheck_setup_callback(s_urlpath)
    except du.CallbackAbortException as e:
        logging.critical(f"ABORTED: setup_snapshot_components() [{e}]")
        return tuple(no_update for _ in range(3))  # type: ignore[return-value]
    else:
        logging.warning(
            f"'{du.triggered()}' -> setup_snapshot_components()  ({s_urlpath=} {s_snap_ts=})"
        )

    snap_options: List[Dict[str, str]] = []
    label_lines: List[html.Label] = []
    snapshots: List[uut.SnapshotInfo] = []

    # Populate List of Snapshots
    try:
        snapshots = src.list_snapshots(du.get_wbs_l1(s_urlpath))
    except DataSourceException:
        pass
    snap_options = [
        {
            "label": f"{si.name} ({utils.get_human_time(si.timestamp, short=True)})",
            "value": si.timestamp,
        }
        for si in snapshots
    ]

    # This was a tab switch w/ a now non-valid snap ts
    if s_snap_ts not in [si.timestamp for si in snapshots]:
        s_snap_ts = ""

    # Selected a Snapshot
    if s_snap_ts:
        snap_info = next(si for si in snapshots if si.timestamp == s_snap_ts)
        human_time = utils.get_human_time(snap_info.timestamp)
        # get lines
        label_lines = [
            html.Label(f"{snap_info.name}"),
            html.Label(
                f"created by {snap_info.creator} — {human_time}"
                if CurrentUser.is_admin()  # only show creator for admins
                else human_time,
                style={"font-size": "75%", "font-style": "italic"},
            ),
        ]

    return snap_options, label_lines, bool(s_snap_ts)


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
        State("url", "pathname"),
        State("wbs-name-snapshot-input", "value"),
        State("wbs-current-snapshot-ts", "value"),
    ],
    prevent_initial_call=True,
)
def handle_make_snapshot(
    _: int,
    __: int,
    ___: int,
    # state(s)
    s_urlpath: str,
    s_name: str,
    s_snap_ts: str,
) -> Tuple[bool, dbc.Toast, str, str]:
    """Handle the naming and creating of a snapshot."""
    logging.warning(f"'{du.triggered()}' -> handle_make_snapshot()")

    if s_snap_ts:  # are we looking at a snapshot?
        return False, None, "", ""

    if du.triggered_id() == "wbs-make-snapshot-button":
        return True, None, "", ""

    if du.triggered_id() in ["wbs-name-snapshot-btn", "wbs-name-snapshot-input"]:
        try:
            src.create_snapshot(du.get_wbs_l1(s_urlpath), s_name)
            return False, "", "", du.RELOAD
        except DataSourceException:
            fail_toast = du.make_toast(
                "Failed to Make Snapshot", du.REFRESH_MSG, du.Color.DANGER
            )
            return False, fail_toast, du.Color.SUCCESS, ""

    raise Exception(f"Unaccounted trigger {du.triggered()}")


# --------------------------------------------------------------------------------------
# Institution Callbacks


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-phds-authors", "value"),
        Output("wbs-faculty", "value"),
        Output("wbs-scientists-post-docs", "value"),
        Output("wbs-grad-students", "value"),
        Output("wbs-cpus", "value"),
        Output("wbs-gpus", "value"),
        Output("wbs-textarea", "value"),
        #
        Output("wbs-h2-sow-table", "children"),
        Output("wbs-h2-inst-textarea", "children"),
        Output("wbs-h2-inst-computing", "children"),
        #
        Output("institution-headcounts-container", "hidden"),
        Output("institution-values-below-table-container", "hidden"),
        #
        Output("wbs-dropdown-institution", "value"),
        Output("wbs-dropdown-institution", "options"),
        #
        Output("wbs-filter-labor", "options"),
        #
        Output("wbs-headcounts-confirm-timestamp", "data"),
        Output("wbs-table-confirm-timestamp", "data"),
        Output("wbs-computing-confirm-timestamp", "data"),
    ],
    [Input("dummy-input-for-setup", "hidden")],  # never triggered
    [
        State("url", "pathname"),
        State("wbs-current-snapshot-ts", "value"),
    ],
)
def setup_institution_components(
    _: bool,
    # state(s)
    s_urlpath: str,
    s_snap_ts: types.DashVal,
) -> Tuple[
    types.DashVal,
    types.DashVal,
    types.DashVal,
    types.DashVal,
    types.DashVal,
    types.DashVal,
    str,
    #
    str,
    str,
    str,
    #
    bool,
    bool,
    #
    types.DashVal,
    List[Dict[str, str]],
    #
    List[Dict[str, str]],
    #
    int,
    int,
    int,
]:
    """Set up institution-related components."""
    try:
        du.precheck_setup_callback(s_urlpath)
    except du.CallbackAbortException as e:
        logging.critical(f"ABORTED: setup_institution_components() [{e}]")
        return tuple(no_update for _ in range(17))  # type: ignore[return-value]
    else:
        logging.warning(
            f"'{du.triggered()}' -> setup_institution_components() ({s_urlpath=} {s_snap_ts=} {CurrentUser.get_summary()=})"
        )

    inst_dc = uut.InstitutionValues(
        phds_authors=0,
        faculty=0,
        scientists_post_docs=0,
        grad_students=0,
        cpus=0,
        gpus=0,
        text="",
        headcounts_confirmed_ts=0,
        table_confirmed_ts=0,
        computing_confirmed_ts=0,
    )

    h2_table = "Collaboration-Wide SOW Table"
    h2_textarea = ""
    h2_computing = ""

    wbs_l1 = du.get_wbs_l1(s_urlpath)
    tconfig = tc.TableConfigParser(wbs_l1)

    def inactive_flag(info: institution_info.Institution) -> str:
        if info.has_mou:
            return ""
        return "inactive: "

    if CurrentUser.is_admin():
        inst_options = [  # always include the abbreviations for admins
            {
                "label": f"{inactive_flag(info)}{short_name} ({info.long_name})",
                "value": short_name,
                # "disabled": not info.has_mou,
            }
            for short_name, info in institution_info.get_institutions_infos().items()
        ]
    else:
        inst_options = [  # only include the user's institution(s)
            {
                "label": inactive_flag(info) + short_name,
                "value": short_name,
                # "disabled": not info.has_mou,
            }
            for short_name, info in institution_info.get_institutions_infos().items()
            if short_name in CurrentUser.get_institutions()
        ]

    labor_options = [
        {"label": f"{abbrev} – {name}", "value": abbrev}
        for name, abbrev in tconfig.get_labor_categories_w_abbrevs()
    ]

    if inst := du.get_inst(s_urlpath):
        h2_table = f"{inst}'s SOW Table"
        h2_textarea = f"{inst}'s Miscellaneous Notes and Descriptions"
        h2_computing = f"{inst}'s Computing Contributions"
        try:
            inst_dc = src.pull_institution_values(wbs_l1, s_snap_ts, inst)
        except DataSourceException:
            inst_dc = uut.InstitutionValues(
                phds_authors=None,
                faculty=None,
                scientists_post_docs=None,
                grad_students=None,
                cpus=None,
                gpus=None,
                text="",
                headcounts_confirmed_ts=0,
                table_confirmed_ts=0,
                computing_confirmed_ts=0,
            )

    return (
        inst_dc.phds_authors,
        inst_dc.faculty,
        inst_dc.scientists_post_docs,
        inst_dc.grad_students,
        inst_dc.cpus if inst_dc.cpus else 0,  # None (blank) -> 0
        inst_dc.gpus if inst_dc.gpus else 0,  # None (blank) -> 0
        inst_dc.text,
        h2_table,
        h2_textarea,
        h2_computing,
        not inst if wbs_l1 == "mo" else True,  # just hide it if not M&O
        not inst if wbs_l1 == "mo" else True,  # just hide it if not M&O
        inst,
        sorted(inst_options, key=lambda d: d["label"]),
        labor_options,
        inst_dc.headcounts_confirmed_ts,
        inst_dc.table_confirmed_ts,
        inst_dc.computing_confirmed_ts,
    )


@app.callback(  # type: ignore[misc]
    Output("url", "pathname"),
    [Input("wbs-dropdown-institution", "value")],  # user/setup_institution_components
    [State("url", "pathname")],
    prevent_initial_call=True,
)
def select_dropdown_institution(inst: types.DashVal, s_urlpath: str) -> str:
    """Refresh if the user selected an institution."""
    logging.warning(
        f"'{du.triggered()}' -> select_dropdown_institution() {inst=} {CurrentUser.get_institutions()=})"
    )
    inst = "" if not inst else inst

    # did anything change?
    if inst == du.get_inst(s_urlpath):
        return no_update  # type: ignore[no-any-return]

    return du.build_urlpath(du.get_wbs_l1(s_urlpath), inst)  # type: ignore[arg-type]


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-institution-values-first-time-flag", "data"),
        #
        Output("wbs-headcounts-timecheck-container", "children"),
        Output("wbs-institution-textarea-timecheck-container", "children"),
        Output("wbs-computing-timecheck-container", "children"),
        #
        Output("wbs-headcounts-confirm-container-container", "hidden"),
        #
        Output("wbs-headcounts-confirm-timestamp", "data"),
        Output("wbs-table-confirm-timestamp", "data"),
        Output("wbs-computing-confirm-timestamp", "data"),
    ],
    [
        Input("wbs-phds-authors", "value"),  # user/setup_institution_components()
        Input("wbs-faculty", "value"),  # user/setup_institution_components()
        Input("wbs-scientists-post-docs", "value"),  # user/setup_institution_components
        Input("wbs-grad-students", "value"),  # user/setup_institution_components()
        Input("wbs-cpus", "value"),  # user/setup_institution_components()
        Input("wbs-gpus", "value"),  # user/setup_institution_components()
        Input("wbs-textarea", "value"),  # user/setup_institution_components()
        #
        Input("wbs-headcounts-confirm-yes", "n_clicks"),  # user-only
        Input("wbs-table-confirm-yes", "n_clicks"),  # user-only
        Input("wbs-computing-confirm-yes", "n_clicks"),  # user-only
    ],
    [
        State("url", "pathname"),
        State("wbs-current-snapshot-ts", "value"),
        #
        State("wbs-data-table", "data"),
        #
        State("wbs-institution-values-first-time-flag", "data"),
        #
        State("wbs-headcounts-confirm-timestamp", "data"),
        State("wbs-table-confirm-timestamp", "data"),
        State("wbs-computing-confirm-timestamp", "data"),
    ],
    prevent_initial_call=True,
)
def push_institution_values(  # pylint: disable=R0913
    phds: types.DashVal,
    faculty: types.DashVal,
    sci: types.DashVal,
    grad: types.DashVal,
    #
    cpus: types.DashVal,
    gpus: types.DashVal,
    text: str,
    #
    _: int,
    __: int,
    ___: int,
    # state(s)
    s_urlpath: str,
    s_snap_ts: types.DashVal,
    #
    s_table: uut.WebTable,
    #
    s_first_time: bool,
    #
    s_hc_conf_ts: int,
    s_table_conf_ts: int,
    s_comp_conf_ts: int,
) -> Tuple[
    bool,
    #
    List[html.Label],
    List[html.Label],
    List[html.Label],
    #
    bool,
    #
    int,
    int,
    int,
]:
    """Push the institution's values."""
    logging.warning(
        f"'{du.triggered()}' -> push_institution_values() ({s_first_time=})"
    )

    # Is there an institution selected?
    if not (inst := du.get_inst(s_urlpath)):  # pylint: disable=C0325
        return (
            False,
            #
            [],
            [],
            [],
            #
            no_update,
            #
            no_update,
            no_update,
            no_update,
        )

    # Are the fields editable?
    if not CurrentUser.is_loggedin_with_permissions():
        return (
            False,
            #
            [],
            [],
            [],
            #
            True,
            #
            no_update,
            no_update,
            no_update,
        )

    # Is this a snapshot?
    if s_snap_ts:
        return (
            False,
            #
            [],
            [],
            [],
            #
            True,
            #
            no_update,
            no_update,
            no_update,
        )

    # check if headcounts are filled out
    hide_hc_btn = None in [phds, faculty, sci, grad]

    # Were the fields just auto-populated for the first time? No need to push data
    if s_first_time:
        return (
            False,
            #
            du.HEADCOUNTS_REQUIRED if hide_hc_btn else [],  # don't show saved at first
            du.timecheck_labels("Notes & Descriptions", "Autosaved"),
            [],  # don't show saved at first
            #
            hide_hc_btn,
            #
            no_update,
            no_update,
            no_update,
        )

    # what're the confirmation timestamps?
    hc_confirmed_ts = du.figure_headcounts_confirmation_ts(s_hc_conf_ts)
    table_conf_ts = du.figure_computing_confirmation_ts(s_table_conf_ts)
    comp_confirmed_ts = du.figure_computing_confirmation_ts(s_comp_conf_ts)

    # push
    try:
        src.push_institution_values(
            du.get_wbs_l1(s_urlpath),
            inst,
            uut.InstitutionValues(
                phds_authors=phds,  # type: ignore[arg-type]
                faculty=faculty,  # type: ignore[arg-type]
                scientists_post_docs=sci,  # type: ignore[arg-type]
                grad_students=grad,  # type: ignore[arg-type]
                cpus=cpus,  # type: ignore[arg-type]
                gpus=gpus,  # type: ignore[arg-type]
                text=text,
                headcounts_confirmed_ts=hc_confirmed_ts,
                table_confirmed_ts=table_conf_ts,
                computing_confirmed_ts=comp_confirmed_ts,
            ),
        )
    except DataSourceException:
        assert len(s_table) == 0  # there's no collection to push to

    return (
        False,
        #
        du.confirmation_saved_label(
            hc_confirmed_ts,
            "Headcounts",
            override=hide_hc_btn,
            override_label=du.HEADCOUNTS_REQUIRED,
        ),
        du.timecheck_labels("Notes & Descriptions", "Autosaved"),
        du.confirmation_saved_label(comp_confirmed_ts, "Computing Contributions"),
        #
        hide_hc_btn,
        #
        hc_confirmed_ts,
        table_conf_ts,
        comp_confirmed_ts,
    )


# --------------------------------------------------------------------------------------
# Other Callbacks


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-data-table", "editable"),
        Output("wbs-new-data-div-1", "hidden"),
        Output("wbs-new-data-div-2", "hidden"),
        Output("wbs-data-table", "row_deletable"),
        Output("wbs-dropdown-institution", "disabled"),
        Output("wbs-admin-zone-div", "hidden"),
        Output("wbs-phds-authors", "disabled"),
        Output("wbs-faculty", "disabled"),
        Output("wbs-scientists-post-docs", "disabled"),
        Output("wbs-grad-students", "disabled"),
        Output("wbs-cpus", "disabled"),
        Output("wbs-gpus", "disabled"),
        Output("wbs-textarea", "disabled"),
        Output("url-user-inst-redirect", "pathname"),
    ],
    [Input("dummy-input-for-setup", "hidden")],  # never triggered
    [State("wbs-current-snapshot-ts", "value"), State("url", "pathname")],
)
def setup_user_dependent_components(
    _: bool,
    # state(s)
    s_snap_ts: types.DashVal,
    s_urlpath: str,
) -> Tuple[
    bool, bool, bool, bool, bool, bool, bool, bool, bool, bool, bool, bool, bool, str
]:
    """Logged-in callback."""
    try:
        du.precheck_setup_callback(s_urlpath)
    except du.CallbackAbortException as e:
        logging.critical(f"ABORTED: setup_user_dependent_components() [{e}]")
        return tuple(no_update for _ in range(14))  # type: ignore[return-value]
    else:
        logging.warning(
            f"'{du.triggered()}' -> setup_user_dependent_components({s_snap_ts=}, {s_urlpath=}, {CurrentUser.get_summary()=})"
        )

    # filter-inst disabled if not admin and less than 2 insts (to pick from)
    dropdown_institution_disabled = (
        not CurrentUser.is_admin() and len(CurrentUser.get_institutions()) < 2
    )

    if s_snap_ts:
        return (
            False,  # data-table NOT editable
            True,  # new-data-div-1 hidden
            True,  # new-data-div-2 hidden
            False,  # row NOT deletable
            dropdown_institution_disabled,
            True,  # wbs-admin-zone-div hidden
            True,  # institution value disabled
            True,  # institution value disabled
            True,  # institution value disabled
            True,  # institution value disabled
            True,  # institution value disabled
            True,  # institution value disabled
            True,  # institution value disabled
            no_update,
        )

    return (
        True,  # data-table editable
        False,  # new-data-div-1 NOT hidden
        False,  # new-data-div-2 NOT hidden
        True,  # row is deletable
        dropdown_institution_disabled,
        not CurrentUser.is_admin(),  # wbs-admin-zone-div hidden if user is not an admin
        False,  # institution value NOT disabled
        False,  # institution value NOT disabled
        False,  # institution value NOT disabled
        False,  # institution value NOT disabled
        False,  # institution value NOT disabled
        False,  # institution value NOT disabled
        False,  # institution value NOT disabled
        no_update,
    )


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-show-all-rows-button", "children"),
        Output("wbs-show-all-rows-button", "color"),
        Output("wbs-show-all-rows-button", "outline"),
        Output("wbs-data-table", "page_size"),
        Output("wbs-data-table", "page_action"),
    ],
    [
        # user/table_data_exterior_controls
        Input("wbs-show-all-rows-button", "n_clicks")
    ],
    [State("url", "pathname")],
    prevent_initial_call=True,
)
def toggle_pagination(
    n_clicks: int,
    # state(s)
    s_urlpath: str,
) -> Tuple[str, str, bool, int, str]:
    """Toggle whether the table is paginated."""
    logging.warning(f"'{du.triggered()}' -> toggle_pagination({n_clicks=})")

    if n_clicks % 2 == 0:
        tconfig = tc.TableConfigParser(du.get_wbs_l1(s_urlpath))
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
    [State("url", "pathname")],
    prevent_initial_call=True,
)
def toggle_hidden_columns(
    n_clicks: int,
    # state(s)
    s_urlpath: str,
) -> Tuple[str, str, bool, List[str]]:
    """Toggle hiding/showing the default hidden columns."""
    logging.warning(f"'{du.triggered()}' -> toggle_hidden_columns()")

    tconfig = tc.TableConfigParser(du.get_wbs_l1(s_urlpath))

    if n_clicks % 2 == 0:
        hiddens = tconfig.get_hidden_columns()
        if du.get_inst(s_urlpath) and not CurrentUser.is_admin():
            hiddens.append(tconfig.const.INSTITUTION)
        return (
            "Show Hidden Columns",
            du.Color.SECONDARY,
            True,
            hiddens,
        )

    always_hidden_columns = tconfig.get_always_hidden_columns()
    return "Show Default Columns", du.Color.DARK, False, always_hidden_columns
