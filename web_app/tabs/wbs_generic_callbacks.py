"""Tab-toggled layout for a specified WBS."""


import logging
from typing import cast, Dict, List, Optional, Tuple, Union

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore[import]
import dash_html_components as html  # type: ignore[import]
import dash_table  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]
from flask_login import current_user  # type: ignore[import]

from ..config import app
from ..data_source import data_source as src
from ..data_source import table_config as tc
from ..data_source.utils import DataSourceException
from ..utils import dash_utils as du
from ..utils.types import (
    DataEntry,
    InstitutionValues,
    Record,
    SnapshotInfo,
    Table,
    TColumns,
    TDDown,
    TDDownCond,
)

# --------------------------------------------------------------------------------------
# Layout


def layout() -> html.Div:
    """Construct the HTML."""
    tconfig = tc.TableConfigParser()  # get fresh table config

    return html.Div(
        children=[
            dbc.Row(
                justify="center",
                style={"margin-bottom": "2.5rem"},
                children=[
                    dbc.Col(
                        width=5,
                        children=[
                            html.Div(children="Institution", className="caps"),
                            # Institution filter dropdown menu
                            dcc.Dropdown(
                                id="wbs-filter-inst",
                                options=[
                                    {"label": f"{abbrev} ({name})", "value": abbrev}
                                    for name, abbrev in tconfig.get_institutions_w_abbrevs()
                                ],
                                value="",
                                disabled=False,
                            ),
                        ],
                    ),
                    dbc.Col(
                        width=5,
                        children=[
                            # Labor Category filter dropdown menu
                            html.Div(children="Labor Category", className="caps"),
                            dcc.Dropdown(
                                id="wbs-filter-labor",
                                options=[
                                    {"label": st, "value": st}
                                    for st in tconfig.get_labor_categories()
                                ],
                                value="",
                            ),
                        ],
                    ),
                ],
            ),
            ####
            # Log-In Alert
            dbc.Alert(
                "— log in to edit —",
                id="wbs-how-to-edit-alert",
                style={
                    "fontWeight": "bold",
                    "fontSize": "20px",
                    "width": "100%",
                    "height": "5rem",
                    "text-align": "center",
                    "border": 0,
                    "background-color": "lightgray",
                    "padding-top": "1.5rem",
                    "margin-bottom": "2.5rem",
                },
                className="caps",
                color=du.Color.DARK,
            ),
            # Add Button
            du.new_data_button(1, style={"margin-bottom": "1rem", "height": "40px"}),
            # "Viewing Snapshot" Alert
            dbc.Alert(
                children=[
                    html.Div(
                        id="wbs-snapshot-current-labels",
                        style={"margin-bottom": "1rem", "color": "#5a5a5a"},
                    ),
                    dbc.Button(
                        "View Live Table",
                        id="wbs-view-live-btn",
                        n_clicks=0,
                        color=du.Color.SUCCESS,
                    ),
                ],
                id="wbs-viewing-snapshot-alert",
                style={
                    "fontWeight": "bold",
                    "fontSize": "20px",
                    "width": "100%",
                    "text-align": "center",
                    "padding": "1.5rem",
                },
                className="caps",
                color=du.Color.LIGHT,
                is_open=False,
            ),
            #
            # Institution Fields
            html.Div(
                id="institution-fields-counts-container",
                hidden=True,
                className="institution-fields-counts-container",
                children=[
                    dbc.Row(
                        align="center",
                        children=[
                            dbc.Col(
                                className="institution-fields-headcount",
                                children=[
                                    html.Div(_label, className="caps"),
                                    dcc.Input(
                                        value=0,
                                        min=0,
                                        id=_id,
                                        className="institution-fields-headcount-input",
                                        type="number",
                                    ),
                                ],
                            )
                            for _id, _label in [
                                ("wbs-phds-authors", "PhDs/Authors"),
                                ("wbs-faculty", "Faculty"),
                                ("wbs-scientists-post-docs", "Scientists/Post-Docs"),
                                ("wbs-grad-students", "Grad Students"),
                            ]
                        ],
                    ),
                ],
            ),
            #
            # Table
            dash_table.DataTable(
                id="wbs-data-table",
                editable=False,
                # sort_action="native",
                # sort_mode="multi",
                # filter_action="native",  # the UI for native filtering isn't there yet
                sort_action="native",
                # Styles
                style_table={
                    "overflowX": "auto",
                    "overflowY": "auto",
                    "padding-left": "1em",
                },
                style_header={
                    "backgroundColor": "black",
                    "color": "whitesmoke",
                    "whiteSpace": "normal",
                    "fontWeight": "normal",
                    "height": "auto",
                    "lineHeight": "15px",
                },
                style_cell={
                    "textAlign": "left",
                    "fontSize": 14,
                    "font-family": "sans-serif",
                    "padding-left": "0.5em",
                    # these widths will make it obvious if there's a new/extra column
                    "minWidth": "10px",
                    "width": "10px",
                    "maxWidth": "10px",
                },
                style_cell_conditional=du.style_cell_conditional(tconfig),
                style_data={
                    "whiteSpace": "normal",
                    "height": "auto",
                    "lineHeight": "20px",
                    "wordBreak": "normal",
                },
                style_data_conditional=du.get_style_data_conditional(tconfig),
                # row_deletable set in callback
                # hidden_columns set in callback
                # page_size set in callback
                # data set in callback
                # columns set in callback
                # dropdown set in callback
                # dropdown_conditional set in callback
                export_format="xlsx",
                export_headers="display",
                merge_duplicate_headers=True,
                # fixed_rows={"headers": True, "data": 0},
            ),
            # Bottom Buttons
            dbc.Row(
                style={"margin-top": "0.8em"},
                children=[
                    # Leftward Buttons
                    dbc.Row(
                        style={"width": "52rem", "margin-left": "0.25rem"},
                        children=[
                            # New Data
                            du.new_data_button(
                                2, style={"width": "15rem", "margin-right": "1rem"},
                            ),
                            dcc.Loading(
                                type="dot",
                                color="#258835",
                                children=[
                                    # Load Snapshot
                                    dbc.Button(
                                        "Load Snapshot",
                                        id="wbs-load-snapshot-button",
                                        n_clicks=0,
                                        outline=True,
                                        color=du.Color.INFO,
                                        style={"margin-right": "1rem"},
                                    ),
                                    # Make Snapshot
                                    dbc.Button(
                                        "Make Snapshot",
                                        id="wbs-make-snapshot-button",
                                        n_clicks=0,
                                        outline=True,
                                        color=du.Color.SUCCESS,
                                        style={"margin-right": "1rem"},
                                    ),
                                ],
                            ),
                            # Refresh
                            dbc.Button(
                                "↻",
                                id="wbs-refresh-button",
                                n_clicks=0,
                                outline=True,
                                color=du.Color.SUCCESS,
                                style={"font-weight": "bold"},
                            ),
                        ],
                    ),
                    # Rightward Buttons
                    dbc.Row(
                        style={"flex-basis": "55%", "justify-content": "flex-end"},
                        children=[
                            dcc.Loading(
                                type="default",
                                fullscreen=True,
                                style={"background": "transparent"},  # float atop all
                                color="#17a2b8",
                                children=[
                                    # Show Totals
                                    dbc.Button(
                                        id="wbs-show-totals-button",
                                        n_clicks=0,
                                        style={"margin-right": "1rem"},
                                    ),
                                    # Show All Columns
                                    dbc.Button(
                                        id="wbs-show-all-columns-button",
                                        n_clicks=0,
                                        style={"margin-right": "1rem"},
                                    ),
                                    # Show All Rows
                                    dbc.Button(
                                        id="wbs-show-all-rows-button",
                                        n_clicks=0,
                                        style={"margin-right": "1rem"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            #
            # Last Refreshed
            dcc.Loading(
                type="default",
                fullscreen=True,
                style={"background": "transparent"},  # float atop all
                color="#17a2b8",
                children=[
                    html.Label(
                        id="wbs-last-updated-label",
                        style={
                            "font-style": "italic",
                            "fontSize": "14px",
                            "margin-top": "2.5rem",
                            "text-align": "center",
                        },
                        className="caps",
                    )
                ],
            ),
            #
            # Free Text
            html.Div(
                id="institution-textarea-container",
                hidden=True,
                style={"margin-top": "2.5rem", "width": "100%", "height": "30rem"},
                children=[
                    html.Div("Notes and Descriptions", className="caps"),
                    dcc.Textarea(
                        id="wbs-textarea", style={"width": "100%", "height": "100%"}
                    ),
                ],
            ),
            #
            # Upload/Override XLSX
            html.Div(
                id="wbs-upload-xlsx-launch-modal-button-div",
                children=[
                    html.Hr(),
                    dbc.Button(
                        "Override Live Table with .xlsx",
                        id="wbs-upload-xlsx-launch-modal-button",
                        block=True,
                        n_clicks=0,
                        color=du.Color.WARNING,
                        disabled=False,
                        style={"margin-bottom": "1rem"},
                    ),
                ],
                hidden=True,
            ),
            #
            # Data Stores aka Cookies
            # - for communicating when table was last updated by an exterior control
            dcc.Store(
                id="wbs-table-exterior-control-last-timestamp", storage_type="memory",
            ),
            # - for caching the table config, to limit REST calls
            dcc.Store(
                id="wbs-table-config-cache", storage_type="memory", data=tconfig.config,
            ),
            # for caching the current snapshot
            dcc.Store(id="wbs-snapshot-current-ts", storage_type="memory", data=""),
            # for caching all snapshots' infos
            dcc.Store(id="wbs-all-snapshot-infos", storage_type="memory"),
            # for caching the visible Institution and its values
            dcc.Store(id="wbs-previous-inst-and-vals", storage_type="memory"),
            #
            # Dummy Divs -- for adding dynamic toasts, dialogs, etc.
            html.Div(id="wbs-toast-via-exterior-control-div"),
            html.Div(id="wbs-toast-via-interior-control-div"),
            html.Div(id="wbs-toast-via-snapshot-div"),
            html.Div(id="wbs-toast-via-upload-div"),
            #
            # Modals & Toasts
            du.load_snapshot_modal(),
            du.deletion_toast(),
            du.upload_modal(),
            du.name_snapshot_modal(),
            ###
        ]
    )


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
    state_table: Table,
    state_columns: TColumns,
    labor: str,
    institution: str,
    state_tconfig_cache: tc.TableConfigParser.Cache,
) -> Tuple[Table, dbc.Toast]:
    """Push new record to data source; add to table.

    Returns:
        TData     -- up-to-date data table
        dbc.Toast -- toast element with confirmation message
    """
    table = state_table
    column_names = [c["name"] for c in state_columns]
    new_record: Record = {n: "" for n in column_names}

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
            "Record Added", f"id: {new_record[src.ID]}", du.Color.SUCCESS, 5
        )
    except DataSourceException:
        toast = du.make_toast("Failed to Make Record", du.REFRESH_MSG, du.Color.DANGER)

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
        Output("institution-fields-counts-container", "hidden"),
        Output("institution-textarea-container", "hidden"),
    ],
    [
        Input("wbs-l1", "value"),
        Input("wbs-filter-inst", "value"),
        Input("wbs-filter-labor", "value"),
        Input("wbs-new-data-button", "n_clicks"),
        Input("wbs-refresh-button", "n_clicks"),
        Input("wbs-show-totals-button", "n_clicks"),
        Input("wbs-snapshot-current-ts", "data"),
        Input("wbs-undo-last-delete", "n_clicks"),
    ],
    [
        State("wbs-data-table", "data"),
        State("wbs-data-table", "columns"),
        State("wbs-show-all-columns-button", "n_clicks"),
        State("wbs-last-deleted-id", "children"),
        State("wbs-table-config-cache", "data"),
    ],
    prevent_initial_call=True,  # triggered instead by Input("wbs-l1", "value")
)  # pylint: disable=R0913,R0914
def table_data_exterior_controls(
    # L1 input (input)
    wbs_l1: str,
    # other input(s)
    institution: str,
    labor: str,
    _: int,
    __: int,
    tot_n_clicks: int,
    snapshot_ts: str,
    ___: int,
    # state(s)
    state_table: Table,
    state_columns: TColumns,
    state_all_cols: int,
    state_deleted_id: str,
    state_tconfig_cache: tc.TableConfigParser.Cache,
) -> Tuple[Table, int, str, dbc.Toast, str, str, bool, int, bool, bool]:
    """Exterior control signaled that the table should be updated.

    This is either a filter, "add new", refresh, or "show totals". Only
    "add new" changes MoU DS data. The others simply change what's
    visible to the user.
    """
    logging.warning("table_data_exterior_controls()")
    logging.warning(
        f"Snapshot: {snapshot_ts=} {'' if snapshot_ts else '(Live Collection)'}"
    )

    table: Table = []
    toast: dbc.Toast = None

    # format "Show Totals" button
    show_totals, tot_label, tot_color, tot_outline, all_cols = _totals_button_logic(
        tot_n_clicks, state_all_cols
    )

    # Add New Data
    if du.triggered_id() == "wbs-new-data-button":
        if not snapshot_ts:  # are we looking at a snapshot?
            table, toast = _add_new_data(
                wbs_l1,
                state_table,
                state_columns,
                labor,
                institution,
                state_tconfig_cache,
            )

    # OR Restore a Record and Pull Table (optionally filtered)
    elif du.triggered_id() == "wbs-undo-last-delete":
        if not snapshot_ts:  # are we looking at a snapshot?
            try:
                table = src.pull_data_table(
                    wbs_l1,
                    institution=institution,
                    labor=labor,
                    with_totals=show_totals,
                    restore_id=state_deleted_id,
                )
                toast = du.make_toast(
                    "Record Restored", f"id: {state_deleted_id}", du.Color.SUCCESS, 5
                )
            except DataSourceException:
                table = []

    # OR Just Pull Table (optionally filtered)
    else:
        try:
            table = src.pull_data_table(
                wbs_l1,
                institution=institution,
                labor=labor,
                with_totals=show_totals,
                snapshot_ts=snapshot_ts,
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
        not institution,
        not institution,
    )


def _push_modified_records(
    wbs_l1: str,
    current_table: Table,
    previous_table: Table,
    state_tconfig_cache: tc.TableConfigParser.Cache,
) -> List[DataEntry]:
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
    wbs_l1: str, current_table: Table, previous_table: Table, keeps: List[DataEntry]
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
            f"Failed to Delete Record {record[src.ID]}",
            du.REFRESH_MSG,
            du.Color.DANGER,
        )

    return toast, last_deletion


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-data-table", "data_previous"),
        Output("wbs-toast-via-interior-control-div", "children"),
        Output("wbs-last-updated-label", "children"),
        Output("wbs-last-deleted-id", "children"),
        Output("wbs-deletion-toast", "is_open"),
    ],
    [Input("wbs-l1", "value"), Input("wbs-data-table", "data")],
    [
        State("wbs-data-table", "data_previous"),
        State("wbs-table-exterior-control-last-timestamp", "data"),
        State("wbs-table-config-cache", "data"),
        State("wbs-snapshot-current-ts", "data"),
    ],
    prevent_initial_call=True,  # triggered instead by Input("wbs-l1", "value")
)
def table_data_interior_controls(
    # L1 value (input)
    wbs_l1: str,
    # other input(s)
    current_table: Table,
    # state(s)
    previous_table: Table,
    table_exterior_control_ts: str,
    state_tconfig_cache: tc.TableConfigParser.Cache,
    state_snap_current_ts: str,
) -> Tuple[Table, dbc.Toast, str, str, bool]:
    """Interior control signaled that the table should be updated.

    This is either a row deletion or a field edit. The table's view has
    already been updated, so only DS communication is needed.

    NOTE: This function is also called following table_data_exterior_controls().
    This is unnecessary, so the timestamp of table_data_exterior_controls()'s
    last call will be checked to determine if that was indeed the case.
    """
    logging.warning("table_data_interior_controls()")

    updated_message = f"Last Refreshed: {du.get_human_now()}"

    # On page load OR table was just updated via exterior controls
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
)
def table_columns(
    # input(s)
    table_editable: bool,
    # state(s)
    state_tconfig_cache: tc.TableConfigParser.Cache,
) -> List[Dict[str, object]]:
    """Grab table columns."""
    logging.warning("table_columns()")

    tconfig = tc.TableConfigParser(state_tconfig_cache)

    def _presentation(col_name: str) -> str:
        if tconfig.is_column_dropdown(col_name):
            return "dropdown"
        return "input"  # default

    def _type(col_name: str) -> str:
        if tconfig.is_column_numeric(col_name):
            return "numeric"
        return "any"  # default

    columns = [
        {
            "id": c,
            "name": c,
            "presentation": _presentation(c),
            "type": _type(c),
            "editable": table_editable and tconfig.is_column_editable(c),
            "hideable": True,
        }
        for c in tconfig.get_table_columns()
    ]

    return columns


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
) -> Tuple[TDDown, TDDownCond]:
    """Grab table dropdowns."""
    logging.warning("table_dropdown()")

    simple_dropdowns: TDDown = {}
    conditional_dropdowns: TDDownCond = []
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
    [
        Output("wbs-load-snapshot-modal", "is_open"),
        Output("wbs-snapshot-selection", "options"),
        Output("wbs-snapshot-current-labels", "children"),
        Output("wbs-snapshot-current-ts", "data"),
        Output("wbs-viewing-snapshot-alert", "is_open"),
        Output("wbs-all-snapshot-infos", "data"),
    ],
    [
        Input("wbs-load-snapshot-button", "n_clicks"),
        Input("wbs-view-live-btn-modal", "n_clicks"),
        Input("wbs-view-live-btn", "n_clicks"),
        Input("wbs-snapshot-selection", "value"),
    ],
    [
        State("wbs-l1", "value"),
        State("wbs-snapshot-current-ts", "data"),
        State("wbs-all-snapshot-infos", "data"),
    ],
    prevent_initial_call=True,
)
def handle_load_snapshot(
    # input(s)
    _: int,
    __: int,
    ___: int,
    snapshot_ts_selection: str,
    # L1 value (state)
    wbs_l1: str,
    # other state(s)
    state_snap_current_ts: str,
    state_all_snap_infos: Dict[str, SnapshotInfo],
) -> Tuple[
    bool, List[dbc.ListGroupItem], List[html.Label], str, bool, Dict[str, SnapshotInfo],
]:
    """Launch snapshot modal, load live table, or select a snapshot.

    Must be one function b/c all triggers control whether the modal is
    open.
    """
    logging.warning("handle_load_snapshot()")

    # Load Live Table
    if du.triggered_id() in ["wbs-view-live-btn-modal", "wbs-view-live-btn"]:
        return False, [], [], "", False, state_all_snap_infos

    # Load Modal List of Snapshots
    if du.triggered_id() == "wbs-load-snapshot-button":
        try:
            snapshots = src.list_snapshots(wbs_l1)
        except DataSourceException:
            snapshots = []
        snapshots_options = [
            {
                "label": f"{snap['name']}  [created by {snap['creator']} on {du.get_human_time(snap['timestamp'])}]",
                "value": snap["timestamp"],
            }
            for snap in snapshots
        ]
        all_snap_infos = {snap["timestamp"]: snap for snap in snapshots}
        return True, snapshots_options, [], state_snap_current_ts, False, all_snap_infos

    # Selected a Snapshot
    info = state_all_snap_infos[snapshot_ts_selection]
    label_lines = [
        html.Label(f"Viewing Snapshot: \"{info['name']}\""),
        html.Label(
            f"(created by {info['creator']} on {du.get_human_time(snapshot_ts_selection)})",
            style={"font-size": "75%", "font-style": "italic"},
        ),
    ]
    return False, [], label_lines, snapshot_ts_selection, True, state_all_snap_infos


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
        State("wbs-snapshot-current-ts", "data"),
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
    logging.warning("handle_make_snapshot()")

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
# Institution Values Callbacks


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-phds-authors", "value"),
        Output("wbs-faculty", "value"),
        Output("wbs-scientists-post-docs", "value"),
        Output("wbs-grad-students", "value"),
        Output("wbs-textarea", "value"),
    ],
    [
        Input("institution-fields-counts-container", "hidden"),
        Input("institution-textarea-container", "hidden"),
    ],
    [
        State("wbs-l1", "value"),
        State("wbs-snapshot-current-ts", "data"),
        State("wbs-filter-inst", "value"),
    ],
    prevent_initial_call=True,
)
def get_institution_values(
    _: bool,
    __: bool,
    # L1 value (state)
    wbs_l1: str,
    # other state(s)
    state_snap_current_ts: str,
    state_institution: str,
) -> Tuple[int, int, int, int, str]:
    """Get the institution's values."""
    logging.warning("get_institution_values()")

    if not state_institution or not current_user.is_authenticated:
        return 0, 0, 0, 0, ""

    try:
        values = src.pull_institution_values(
            wbs_l1, state_snap_current_ts, state_institution
        )
        return (
            values["phds_authors"],
            values["faculty"],
            values["scientists_post_docs"],
            values["grad_students"],
            values["text"],
        )

    except DataSourceException:
        return 0, 0, 0, 0, ""


@app.callback(  # type: ignore[misc]
    Output("wbs-previous-inst-and-vals", "data"),
    [
        Input("wbs-phds-authors", "value"),
        Input("wbs-faculty", "value"),
        Input("wbs-scientists-post-docs", "value"),
        Input("wbs-grad-students", "value"),
        Input("wbs-textarea", "value"),
    ],
    [
        State("wbs-l1", "value"),
        State("wbs-filter-inst", "value"),
        State("wbs-snapshot-current-ts", "data"),
        State("wbs-previous-inst-and-vals", "data"),
        State("wbs-data-table", "data"),
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
    state_institution: str,
    state_snap_current_ts: str,
    prev_inst_and_vals: Dict[str, Union[str, InstitutionValues]],
    state_table: Table,
) -> Dict[str, Union[str, InstitutionValues]]:
    """Push the institution's values."""
    logging.warning("push_institution_values()")

    if (not state_institution) or (not current_user.is_authenticated):
        return {}

    # are we looking at a snapshot?
    if state_snap_current_ts:
        return prev_inst_and_vals

    values: InstitutionValues = {
        "phds_authors": phds_authors,
        "faculty": faculty,
        "scientists_post_docs": scientists_post_docs,
        "grad_students": grad_students,
        "text": text,
    }

    # check if anything actually changed
    if (
        prev_inst_and_vals
        and state_institution == prev_inst_and_vals["inst"]
        and values == prev_inst_and_vals["vals"]
    ):
        logging.warning(
            f"pushing institution values suppressed (no change) {prev_inst_and_vals}"
        )
        return prev_inst_and_vals

    try:
        src.push_institution_values(wbs_l1, state_institution, values)
    except DataSourceException:
        assert len(state_table) == 0  # there's no collection to push to

    return {"inst": state_institution, "vals": values}


# --------------------------------------------------------------------------------------
# Other Callbacks


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
        # pylint: disable=C0325
        error, n_records, prev_snap, curr_snap = src.override_table(
            wbs_l1, base64_file, filename
        )
        if error:
            error_message = f'Error overriding "{filename}" ({error})'
            return True, error_message, du.Color.DANGER, True, 0, None
        success_toast = du.make_toast(
            f'Live Table Updated with "{filename}"',
            _get_ingest_sucess_message(n_records, prev_snap, curr_snap),
            du.Color.SUCCESS,
        )
        return False, "", "", True, 1, success_toast

    raise Exception(f"Unaccounted for trigger {du.triggered_id()}")


@app.callback(  # type: ignore[misc]
    [
        Output("wbs-data-table", "editable"),
        Output("wbs-new-data-div-1", "hidden"),
        Output("wbs-new-data-div-2", "hidden"),
        Output("wbs-make-snapshot-button", "hidden"),
        Output("wbs-how-to-edit-alert", "hidden"),
        Output("wbs-data-table", "row_deletable"),
        Output("wbs-filter-inst", "disabled"),
        Output("wbs-filter-inst", "value"),
        Output("wbs-upload-xlsx-launch-modal-button-div", "hidden"),
        Output("wbs-phds-authors", "disabled"),
        Output("wbs-faculty", "disabled"),
        Output("wbs-scientists-post-docs", "disabled"),
        Output("wbs-grad-students", "disabled"),
        Output("wbs-textarea", "disabled"),
    ],
    [Input("wbs-viewing-snapshot-alert", "is_open"), Input("logout-div", "hidden")],
)
def login_actions(
    # input(s)
    viewing_snapshot: bool,
    _: bool,
) -> Tuple[
    bool, bool, bool, bool, bool, bool, bool, str, bool, bool, bool, bool, bool, bool
]:
    """Logged-in callback."""
    logging.warning("login_actions()")

    if viewing_snapshot:
        return (
            False,  # data-table NOT editable
            True,  # new-data-div-1 hidden
            True,  # new-data-div-2 hidden
            True,  # make-snapshot-button hidden
            True,  # how-to-edit-alert hidden
            False,  # row NOT deletable
            False,  # filter-inst NOT disabled
            current_user.institution if current_user.is_authenticated else "",
            True,  # upload-xlsx-override-div hidden
            True,
            True,
            True,
            True,
            True,
        )

    if current_user.is_authenticated:
        return (
            True,  # data-table editable
            False,  # new-data-div-1 NOT hidden
            False,  # new-data-div-2 NOT hidden
            False,  # make-snapshot-button NOT hidden
            True,  # how-to-edit-alert hidden
            True,  # row is deletable
            not current_user.is_admin,  # filter-inst disabled if user is not an admin
            current_user.institution,
            not current_user.is_admin,  # upload-xlsx-override-div hidden if user is not an admin
            False,
            False,
            False,
            False,
            False,
        )
    return (
        False,  # data-table NOT editable
        True,  # new-data-div-1 hidden
        True,  # new-data-div-2 hidden
        True,  # make-snapshot-button hidden
        False,  # how-to-edit-alert NOT hidden
        False,  # row NOT deletable
        False,  # filter-inst NOT disabled
        "",
        True,  # upload-xlsx-override-div hidden
        True,
        True,
        True,
        True,
        True,
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
    logging.warning("toggle_pagination()")

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
)
def toggle_hidden_columns(
    # input(s)
    n_clicks: int,
    # state(s)
    state_tconfig_cache: tc.TableConfigParser.Cache,
) -> Tuple[str, str, bool, List[str]]:
    """Toggle hiding/showing the default hidden columns."""
    logging.warning("toggle_hidden_columns()")

    if n_clicks % 2 == 0:
        tconfig = tc.TableConfigParser(state_tconfig_cache)
        return (
            "Show Hidden Columns",
            du.Color.SECONDARY,
            True,
            tconfig.get_hidden_columns(),
        )
    return "Show Default Columns", du.Color.DARK, False, []
