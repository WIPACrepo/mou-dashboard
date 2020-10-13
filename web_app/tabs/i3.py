"""Conditional in-cell drop-down menu with IceCube WBS MoU info."""


from typing import cast, Dict, List, Tuple

import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore[import]
import dash_html_components as html  # type: ignore[import]
import dash_table  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]
from flask_login import current_user  # type: ignore[import]

from ..config import app
from ..utils import dash_utils as util
from ..utils import data_source as src
from ..utils.types import DataEntry, Record, Table, TColumns, TDDown, TDDownCond, TFocus

# --------------------------------------------------------------------------------------
# Layout


def layout() -> html.Div:
    """Construct the HTML."""
    tconfig = src.TableConfigParser()  # get fresh table config

    return html.Div(
        children=[
            dbc.Row(
                justify="center",
                style={"margin-bottom": "2.5rem"},
                children=[
                    dbc.Col(
                        width=5,
                        # style=WIDTH_45,
                        children=[
                            html.Div(children="Institution", className="caps"),
                            # Institution filter dropdown menu
                            dcc.Dropdown(
                                id="tab-1-filter-inst",
                                options=[
                                    {"label": f"{abbrev} ({name})", "value": abbrev}
                                    for name, abbrev in tconfig.get_institutions_w_abbrevs()
                                ],
                                value="",
                                # multi=True
                                disabled=False,
                            ),
                        ],
                    ),
                    dbc.Col(
                        width=5,
                        # style=WIDTH_45,
                        children=[
                            # Labor Category filter dropdown menu
                            html.Div(children="Labor Category", className="caps"),
                            dcc.Dropdown(
                                id="tab-1-filter-labor",
                                options=[
                                    {"label": st, "value": st}
                                    for st in tconfig.get_labor_categories()
                                ],
                                value="",
                                # multi=True
                            ),
                        ],
                    ),
                ],
            ),
            ####
            # html.Hr(style=SHORT_HR),
            ####
            # Sign-In Alert
            dbc.Alert(
                "- log in to edit -",
                id="tab-1-how-to-edit-alert",
                style={
                    "fontWeight": "bold",
                    "fontSize": "20px",
                    "width": "100%",
                    "text-align": "center",
                },
                className="caps",
                color=util.Color.DARK,
            ),
            # Add Button
            util.new_data_button(1, style={"margin-bottom": "1rem", "height": "40px"}),
            # "Viewing Snapshot" Alert
            dbc.Alert(
                [
                    html.Div("Viewing Snapshot", style={"margin-bottom": "0.5rem"}),
                    html.Div(
                        id="tab-1-snapshot-human", style={"margin-bottom": "0.5rem"}
                    ),
                    html.Div(id="tab-1-snapshot-timestamp", hidden=True),
                    dbc.Button(
                        "View Live Table",
                        id="tab-1-view-live-btn",
                        n_clicks=0,
                        color=util.Color.SUCCESS,
                    ),
                ],
                id="tab-1-viewing-snapshot-alert",
                style={
                    "fontWeight": "bold",
                    "fontSize": "20px",
                    "width": "100%",
                    "text-align": "center",
                },
                className="caps",
                color=util.Color.LIGHT,
                is_open=False,
            ),
            # Table
            dash_table.DataTable(
                id="tab-1-data-table",
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
                    "backgroundColor": "#6C757D",
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
                style_cell_conditional=util.style_cell_conditional(tconfig),
                style_data={
                    "whiteSpace": "normal",
                    "height": "auto",
                    "lineHeight": "20px",
                    "wordBreak": "normal",
                },
                style_data_conditional=util.get_style_data_conditional(tconfig),
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
                            util.new_data_button(
                                2, style={"width": "15rem", "margin-right": "1rem"}
                            ),
                            # Load Snapshot
                            dbc.Button(
                                "Load Snapshot",
                                id="tab-1-load-snapshot-button",
                                n_clicks=0,
                                outline=True,
                                color=util.Color.INFO,
                                style={"margin-right": "1rem"},
                            ),
                            # Make Snapshot
                            dbc.Button(
                                "Make Snapshot",
                                id="tab-1-make-snapshot-button",
                                n_clicks=0,
                                outline=True,
                                color=util.Color.SUCCESS,
                                style={"margin-right": "1rem"},
                            ),
                            # Refresh
                            dbc.Button(
                                "↻",
                                id="tab-1-refresh-button",
                                n_clicks=0,
                                outline=True,
                                color=util.Color.SUCCESS,
                                style={"font-weight": "bold"},
                            ),
                        ],
                    ),
                    # Rightward Buttons
                    dbc.Row(
                        style={"flex-basis": "55%", "justify-content": "flex-end"},
                        children=[
                            # Show Totals
                            dbc.Button(
                                id="tab-1-show-totals-button",
                                n_clicks=0,
                                style={"margin-right": "1rem"},
                            ),
                            # Show All Columns
                            dbc.Button(
                                id="tab-1-show-all-columns-button",
                                n_clicks=0,
                                style={"margin-right": "1rem"},
                            ),
                            # Show All Rows
                            dbc.Button(
                                id="tab-1-show-all-rows-button",
                                n_clicks=0,
                                style={"margin-right": "1rem"},
                            ),
                        ],
                    ),
                ],
            ),
            dbc.Row(
                html.Label(
                    id="tab-1-last-updated-label",
                    style={"font-style": "italic", "fontSize": "14px"},
                    className="caps",
                ),
                justify="center",
                style={"margin-top": "15px"},
            ),
            html.Div(
                id="tab-1-upload-xlsx-launch-modal-button-div",
                children=[
                    html.Hr(),
                    dbc.Button(
                        "Override Live Table with .xlsx",
                        id="tab-1-upload-xlsx-launch-modal-button",
                        block=True,
                        n_clicks=0,
                        color=util.Color.WARNING,
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
                id="tab-1-table-exterior-control-last-timestamp", storage_type="memory",
            ),
            # - for caching the table config, to limit REST calls
            dcc.Store(
                id="tab-1-table-config-cache",
                storage_type="memory",
                data=tconfig.config,
            ),
            #
            # Dummy Divs -- for adding dynamic toasts, dialogs, etc.
            html.Div(id="tab-1-toast-via-exterior-control-div"),
            html.Div(id="tab-1-toast-via-interior-control-div"),
            html.Div(id="tab-1-toast-via-snapshot-div"),
            html.Div(id="tab-1-toast-via-upload-div"),
            #
            # Modals & Toasts
            util.snapshot_modal(),
            util.deletion_toast(),
            util.upload_modal(),
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
        int  -- auto n_clicks for "tab-1-show-all-columns-button"
    """
    on = n_clicks % 2 == 1  # pylint: disable=C0103
    triggered = util.triggered_id() == "tab-1-show-totals-button"

    if not on:  # off -> don't trigger "show-all-columns"
        return False, "Show Totals", util.Color.SECONDARY, True, state_all_cols

    if triggered:  # on and triggered -> trigger "show-all-columns"
        return True, "Hide Totals", util.Color.DARK, False, 1

    # on and not triggered, AKA already on -> don't trigger "show-all-columns"
    return True, "Hide Totals", util.Color.DARK, False, state_all_cols


def _add_new_data(
    state_table: Table, state_columns: TColumns, labor: str, institution: str,
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
    if new_record := src.push_record(new_record, labor=labor, institution=institution, novel=True):  # type: ignore[assignment]
        table.insert(0, new_record)
        toast = util.make_toast(
            "Record Added", f"id: {new_record[src.ID]}", util.Color.SUCCESS, 5
        )
    else:
        toast = util.make_toast(
            "Failed to Make Record", util.REFRESH_MSG, util.Color.DANGER
        )

    return table, toast


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-data-table", "data"),
        Output("tab-1-data-table", "active_cell"),
        Output("tab-1-data-table", "page_current"),
        Output("tab-1-table-exterior-control-last-timestamp", "data"),
        Output("tab-1-toast-via-exterior-control-div", "children"),
        Output("tab-1-show-totals-button", "children"),
        Output("tab-1-show-totals-button", "color"),
        Output("tab-1-show-totals-button", "outline"),
        Output("tab-1-show-all-columns-button", "n_clicks"),
    ],
    [
        Input("tab-1-filter-inst", "value"),
        Input("tab-1-filter-labor", "value"),
        Input("tab-1-new-data-button", "n_clicks"),
        Input("tab-1-refresh-button", "n_clicks"),
        Input("tab-1-show-totals-button", "n_clicks"),
        Input("tab-1-snapshot-timestamp", "children"),
        Input("tab-1-undo-last-delete", "n_clicks"),
    ],
    [
        State("tab-1-data-table", "data"),
        State("tab-1-data-table", "columns"),
        State("tab-1-show-all-columns-button", "n_clicks"),
        State("tab-1-last-deleted-id", "children"),
    ],
)  # pylint: disable=R0913,R0914
def table_data_exterior_controls(
    # inputs
    institution: str,
    labor: str,
    _: int,
    __: int,
    tot_n_clicks: int,
    snapshot: str,
    ___: int,
    # states
    state_table: Table,
    state_columns: TColumns,
    state_all_cols: int,
    state_deleted_id: str,
) -> Tuple[Table, TFocus, int, str, dbc.Toast, str, str, bool, int]:
    """Exterior control signaled that the table should be updated.

    This is either a filter, "add new", refresh, or "show totals". Only
    "add new" changes MoU DS data. The others simply change what's
    visible to the user.
    """
    table: Table = []
    focus: TFocus = None
    toast: dbc.Toast = None

    # focus on first cell, but not on page load
    if current_user.is_authenticated and util.triggered_id() in [
        "tab-1-filter-inst",
        "tab-1-filter-labor",
        "tab-1-new-data-button",
        "tab-1-refresh-button",
        "tab-1-show-totals-button",
    ]:
        focus = {"row": 0, "column": 0}

    # format "Show Totals" button
    show_totals, tot_label, tot_color, tot_outline, all_cols = _totals_button_logic(
        tot_n_clicks, state_all_cols
    )

    # Add New Data
    if util.triggered_id() == "tab-1-new-data-button":
        table, toast = _add_new_data(state_table, state_columns, labor, institution)
    # OR Restore a Record and Pull Table (optionally filtered)
    elif util.triggered_id() == "tab-1-undo-last-delete":
        table = src.pull_data_table(
            institution=institution,
            labor=labor,
            with_totals=show_totals,
            snapshot=snapshot,
            restore_id=state_deleted_id,
        )
        toast = util.make_toast(
            "Record Restored", f"id: {state_deleted_id}", util.Color.SUCCESS
        )
    # OR Just Pull Table (optionally filtered)
    else:
        table = src.pull_data_table(
            institution=institution,
            labor=labor,
            with_totals=show_totals,
            snapshot=snapshot,
        )

    return (
        table,
        focus,
        0,
        util.get_now(),
        toast,
        tot_label,
        tot_color,
        tot_outline,
        all_cols,
    )


def _push_modified_records(
    current_table: Table, previous_table: Table
) -> List[DataEntry]:
    """For each row that changed, push the record to the DS."""
    modified_records = [
        r for r in current_table if (r not in previous_table) and (src.ID in r)
    ]
    for record in modified_records:
        src.push_record(record)

    ids = [c[src.ID] for c in modified_records]
    return ids


def _delete_deleted_records(
    current_table: Table, previous_table: Table, keeps: List[DataEntry]
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
        # try to delete
        if not src.delete_record(cast(str, record[src.ID])):
            failures.append(record)
        else:
            last_deletion = cast(str, record[src.ID])

    # make toast message if any records failed to be deleted
    if failures:
        toast = util.make_toast(
            f"Failed to Delete Record {record[src.ID]}",
            util.REFRESH_MSG,
            util.Color.DANGER,
        )

    return toast, last_deletion


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-data-table", "data_previous"),
        Output("tab-1-toast-via-interior-control-div", "children"),
        Output("tab-1-last-updated-label", "children"),
        Output("tab-1-last-deleted-id", "children"),
        Output("tab-1-deletion-toast", "is_open"),
    ],
    [Input("tab-1-data-table", "data")],
    [
        State("tab-1-data-table", "data_previous"),
        State("tab-1-table-exterior-control-last-timestamp", "data"),
    ],
)
def table_data_interior_controls(
    current_table: Table, previous_table: Table, table_exterior_control_ts: str,
) -> Tuple[Table, dbc.Toast, str, str, bool]:
    """Interior control signaled that the table should be updated.

    This is either a row deletion or a field edit. The table's view has
    already been updated, so only DS communication is needed.

    NOTE: This function is also called following table_data_exterior_controls().
    This is unnecessary, so the timestamp of table_data_exterior_controls()'s
    last call will be checked to determine if that was indeed the case.
    """
    updated_message = f"Last Updated: {util.get_human_now()}"

    # On page load OR table was just updated via exterior controls
    if (not previous_table) or util.was_recent(table_exterior_control_ts):
        return current_table, None, updated_message, "", False

    # Push (if any)
    mod_ids = _push_modified_records(current_table, previous_table)

    # Delete (if any)
    toast, last_deletion = _delete_deleted_records(
        current_table, previous_table, mod_ids
    )

    # Update data_previous
    return current_table, toast, updated_message, last_deletion, bool(last_deletion)


@app.callback(  # type: ignore[misc]
    Output("tab-1-data-table", "columns"),
    [Input("tab-1-data-table", "editable")],
    [State("tab-1-table-config-cache", "data")],
)
def table_columns(
    table_editable: bool, tconfig_state: src.TableConfigParser.Cache
) -> List[Dict[str, object]]:
    """Grab table columns."""
    tconfig = src.TableConfigParser(tconfig_state)

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
        Output("tab-1-data-table", "dropdown"),
        Output("tab-1-data-table", "dropdown_conditional"),
    ],
    [Input("tab-1-data-table", "editable")],
    [State("tab-1-table-config-cache", "data")],
)
def table_dropdown(
    _: bool, tconfig_state: src.TableConfigParser.Cache
) -> Tuple[TDDown, TDDownCond]:
    """Grab table dropdowns."""
    simple_dropdowns: TDDown = {}
    conditional_dropdowns: TDDownCond = []
    tconfig = src.TableConfigParser(tconfig_state)

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
            parent_col, parent_col_opts = tconfig.get_conditional_column_parent(col)
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
        Output("tab-1-load-snapshot-modal", "is_open"),
        Output("tab-1-snapshot-selection", "options"),
        Output("tab-1-snapshot-human", "children"),
        Output("tab-1-snapshot-timestamp", "children"),
        Output("tab-1-viewing-snapshot-alert", "is_open"),
    ],
    [
        Input("tab-1-load-snapshot-button", "n_clicks"),
        Input("tab-1-view-live-btn-modal", "n_clicks"),
        Input("tab-1-view-live-btn", "n_clicks"),
        Input("tab-1-snapshot-selection", "value"),
    ],
    [State("tab-1-snapshot-timestamp", "children")],
    prevent_initial_call=True,
)
def manage_snpshots(
    _: int, __: int, ___: int, snapshot: str, state_snapshot: str
) -> Tuple[bool, List[dbc.ListGroupItem], str, str, bool]:
    """Launch snapshot modal, load live table, or select a snapshot.

    Must be one function b/c all triggers control whether the modal is
    open.
    """
    #
    # Load Live Table
    if util.triggered_id() in ["tab-1-view-live-btn-modal", "tab-1-view-live-btn"]:
        return False, [], "", state_snapshot, False

    # Load Modal List of Snapshots
    if util.triggered_id() == "tab-1-load-snapshot-button":
        snapshots_options = [
            {"label": util.get_human_time(ts), "value": ts}
            for ts in src.list_snapshot_timestamps()
        ]
        return True, snapshots_options, "", state_snapshot, False

    # Selected a Snapshot
    return False, [], f"({util.get_human_time(snapshot)})", snapshot, True


@app.callback(  # type: ignore[misc]
    Output("tab-1-toast-via-snapshot-div", "children"),
    [Input("tab-1-make-snapshot-button", "n_clicks")],
    prevent_initial_call=True,
)
def make_snapshot(_: int) -> dcc.ConfirmDialog:
    """Launch a dialog for not-yet-implemented features."""
    if snapshot := src.create_snapshot():
        return util.make_toast(
            "Snapshot Created", util.get_human_time(snapshot), util.Color.SUCCESS
        )
    return util.make_toast(
        "Failed to Make Snapshot", util.REFRESH_MSG, util.Color.DANGER
    )


# --------------------------------------------------------------------------------------
# Other Callbacks


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-upload-xlsx-modal", "is_open"),
        Output("tab-1-upload-xlsx-filename-alert", "children"),
        Output("tab-1-upload-xlsx-filename-alert", "color"),
        Output("tab-1-upload-xlsx-override-table", "disabled"),
        Output("tab-1-refresh-button", "n_clicks"),
        Output("tab-1-toast-via-upload-div", "children"),
    ],
    [
        Input("tab-1-upload-xlsx-launch-modal-button", "n_clicks"),
        Input("tab-1-upload-xlsx", "contents"),
        Input("tab-1-upload-xlsx-cancel", "n_clicks"),
        Input("tab-1-upload-xlsx-override-table", "n_clicks"),
    ],
    [State("tab-1-upload-xlsx", "filename")],
    prevent_initial_call=True,
)
def handle_xlsx(
    _: int, contents: str, __: int, ___: int, filename: str,
) -> Tuple[bool, str, str, bool, int, dbc.Toast]:
    """Manage uploading a new xlsx document as the new live table."""
    if util.triggered_id() == "tab-1-upload-xlsx-launch-modal-button":
        return True, "", "", True, 0, None

    if util.triggered_id() == "tab-1-upload-xlsx-cancel":
        return False, "", "", True, 0, None

    if util.triggered_id() == "tab-1-upload-xlsx":
        if not filename.endswith(".xlsx"):
            return (
                True,
                f'"{filename}" is not an .xlsx file',
                util.Color.DANGER,
                True,
                0,
                None,
            )
        return True, f'Uploaded "{filename}"', util.Color.SUCCESS, False, 0, None

    if util.triggered_id() == "tab-1-upload-xlsx-override-table":
        base64_file = contents.split(",")[1]
        # pylint: disable=C0325
        error, n_records, previous, current = src.override_table(base64_file, filename)
        if error:
            error_message = f'Error overriding "{filename}" ({error})'
            return True, error_message, util.Color.DANGER, True, 0, None
        success_toast = util.make_toast(
            f'Live Table Updated with "{filename}"',
            f"Uploaded {n_records} records.\n"
            f"A snapshot was made of "
            f"{f'the previous ({util.get_human_time(previous)}) table and ' if previous else ''}"
            f"the current ({util.get_human_time(current)}) table.\n",
            util.Color.SUCCESS,
        )
        return False, "", "", True, 1, success_toast

    raise Exception(f"Unaccounted for trigger {util.triggered_id()}")


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-data-table", "editable"),
        Output("tab-1-new-data-div-1", "hidden"),
        Output("tab-1-new-data-div-2", "hidden"),
        Output("tab-1-make-snapshot-button", "hidden"),
        Output("tab-1-how-to-edit-alert", "hidden"),
        Output("tab-1-data-table", "row_deletable"),
        Output("tab-1-filter-inst", "disabled"),
        Output("tab-1-filter-inst", "value"),
        Output("tab-1-upload-xlsx-launch-modal-button-div", "hidden"),
    ],
    [Input("tab-1-viewing-snapshot-alert", "is_open"), Input("logout-div", "hidden")],
)
def log_in_actions(
    viewing_snapshot: bool, _: bool,
) -> Tuple[bool, bool, bool, bool, bool, bool, bool, str, bool]:
    """Logged-in callback."""
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
    )


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-show-all-rows-button", "children"),
        Output("tab-1-show-all-rows-button", "color"),
        Output("tab-1-show-all-rows-button", "outline"),
        Output("tab-1-data-table", "page_size"),
        Output("tab-1-data-table", "page_action"),
    ],
    [Input("tab-1-show-all-rows-button", "n_clicks")],
    [State("tab-1-table-config-cache", "data")],
)
def toggle_pagination(
    n_clicks: int, tconfig_state: src.TableConfigParser.Cache
) -> Tuple[str, str, bool, int, str]:
    """Toggle whether the table is paginated."""
    if n_clicks % 2 == 0:
        tconfig = src.TableConfigParser(tconfig_state)
        return (
            "Show All Rows",
            util.Color.SECONDARY,
            True,
            tconfig.get_page_size(),
            "native",
        )
    # https://community.plotly.com/t/rendering-all-rows-without-pages-in-datatable/15605/2
    return "Collapse Rows to Pages", util.Color.DARK, False, 9999999999, "none"


@app.callback(  # type: ignore[misc]
    [
        Output("tab-1-show-all-columns-button", "children"),
        Output("tab-1-show-all-columns-button", "color"),
        Output("tab-1-show-all-columns-button", "outline"),
        Output("tab-1-data-table", "hidden_columns"),
    ],
    [Input("tab-1-show-all-columns-button", "n_clicks")],
    [State("tab-1-table-config-cache", "data")],
)
def toggle_hidden_columns(
    n_clicks: int, tconfig_state: src.TableConfigParser.Cache
) -> Tuple[str, str, bool, List[str]]:
    """Toggle hiding/showing the default hidden columns."""
    if n_clicks % 2 == 0:
        tconfig = src.TableConfigParser(tconfig_state)
        return (
            "Show Hidden Columns",
            util.Color.SECONDARY,
            True,
            tconfig.get_hidden_columns(),
        )
    return "Show Default Columns", util.Color.DARK, False, []
