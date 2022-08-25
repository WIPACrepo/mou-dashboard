"""Tab-toggled layout for a specified WBS."""


import dash_bootstrap_components as dbc  # type: ignore[import]
from dash import dash_table, dcc, html  # type: ignore[import]

from ..utils import dash_utils as du


def layout() -> html.Div:
    """Construct the HTML."""
    return html.Div(
        children=[
            html.Div(id="dummy-input-for-setup", hidden=True),
            #
            # PDF User Guide
            dbc.Alert(
                className="caps",
                color=du.Color.DARK,
                style={
                    "fontWeight": "bold",
                    "fontStyle": "italic",
                    "width": "100%",
                    "text-align": "center",
                    "margin-bottom": "1rem",
                },
                children=html.A(
                    "Download User Guide PDF",
                    download="MoU_Dashboard_Getting_Started.pdf",
                    href="/assets/MoU_Dashboard_Getting_Started.pdf",
                ),
            ),
            #
            # "Viewing Snapshot" Alert
            dbc.Alert(
                children=[
                    html.Label(
                        "— Viewing Snapshot —",
                        style={
                            "font-size": "3rem",
                            "color": "#5a5a5a",
                            "font-weight": "100",
                            "margin-bottom": "1rem",
                        },
                    ),
                    html.Div(
                        id="wbs-snapshot-current-labels",
                        style={"margin-bottom": "1.5rem", "color": "#5a5a5a"},
                    ),
                ],
                id="wbs-viewing-snapshot-alert",
                style={
                    "fontWeight": "bold",
                    "fontSize": "20px",
                    "width": "100%",
                    "text-align": "center",
                    "padding": "1.5rem",
                    "padding-bottom": "0.5rem",
                    "margin-bottom": "2rem",
                },
                className="caps",
                color=du.Color.LIGHT,
                is_open=False,
            ),
            #
            # Snapshot / Institution filter dropdown menu / Last Updated label
            dbc.Row(
                className="g-0",  # "g-0" -> no gutters
                children=[
                    dbc.Col(
                        width=4,
                        children=[
                            html.I(
                                id="wbs-view-snapshots",
                                n_clicks=0,
                                className="fa fa-calendar-alt snapshot-icon top-corner",
                                hidden=True,
                            ),
                            dbc.Tooltip(
                                "click to select and view past statements of work",
                                target="wbs-view-snapshots",
                                placement="right",
                                style={"font-size": 15, "maxWidth": 600, "width": 350},
                            ),
                            html.Div(
                                id="wbs-snapshot-dropdown-div",
                                hidden=True,
                                children=dcc.Dropdown(
                                    id="wbs-current-snapshot-ts",
                                    className="snapshot-dropdown",
                                    placeholder="Select Snapshot",
                                    value="",
                                    disabled=False,
                                    persistence=True,
                                    searchable=False,
                                ),
                            ),
                            html.Div(
                                id="wbs-view-live-btn-div",
                                hidden=True,
                                style={"margin-top": "0.25rem"},
                                children=dbc.Button(
                                    "View Today's SOW",
                                    id="wbs-view-live-btn",
                                    n_clicks=0,
                                    color=du.Color.SUCCESS,
                                ),
                            ),
                        ],
                    ),
                    dbc.Col(
                        className="large-dropdown-container",
                        children=[
                            dcc.Dropdown(
                                id="wbs-dropdown-institution",
                                className="large-dropdown institution-dropdown",
                                placeholder="— Viewing Entire Collaboration —",
                                # options set in callback
                                # values set in callback
                                disabled=True,
                                # persistence=True, # not working b/c "value" listed in output of initial-active callback (DASH BUG)
                                clearable=False,
                            ),
                        ],
                    ),
                    dbc.Col(
                        width=4,
                        children=[
                            dcc.Loading(
                                type="default",
                                color=du.TEAL,
                                style={
                                    "right": "0px",
                                    "position": "absolute",
                                    "height": "2rem",
                                },
                                children=[
                                    html.Div(
                                        className="sow-last-updated",
                                        children=[
                                            html.Div(id="wbs-sow-last-updated"),
                                            html.Div(id="wbs-sow-last-updated-time"),
                                        ],
                                    ),
                                ],
                            )
                        ],
                    ),
                ],
            ),
            #
            # Headcounts
            html.Div(
                className="institution-headcounts-inner-container",
                id="institution-headcounts-container",
                hidden=True,
                children=[
                    # Inputs
                    dbc.Row(
                        justify="center",
                        className="g-0",  # "g-0" -> no gutters
                        children=[
                            dbc.Col(
                                className="institution-headcount",
                                children=[
                                    html.Div(_label, className="caps"),
                                    dcc.Input(
                                        id=_id,
                                        className="institution-headcount-input",
                                        type="number",
                                        min=0,
                                        disabled=True,
                                    ),
                                ],
                            )
                            for _id, _label in [
                                ("wbs-phds-authors", "PhDs/Authors"),
                                ("wbs-faculty", "Faculty"),
                                (
                                    "wbs-scientists-post-docs",
                                    "Scientists/Post-Docs",
                                ),
                                ("wbs-grad-students", "Grad Students"),
                            ]
                        ],
                    ),
                    # Autosaved & Confirm
                    du.make_timecheck_container("wbs-headcounts-timecheck-container"),
                    html.Div(
                        id="wbs-headcounts-confirm-container-container",
                        children=du.make_confirm_container(
                            "headcounts", "Submit Headcounts"
                        ),
                    ),
                ],
            ),
            #
            html.H2(className="section-header", id="wbs-h2-sow-table"),
            #
            # Top Tools
            dbc.Row(
                className="g-0 wbs-table-top-toolbar",  # "g-0" -> no gutters
                children=[
                    # Add Button
                    du.new_data_button(1),
                    # Labor Category filter dropdown menu
                    dcc.Dropdown(
                        id="wbs-filter-labor",
                        placeholder="Filter by Labor Category",
                        className="table-tool-large",
                        # options set in callback
                        # vale set in callback
                        optionHeight=30,
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
                    # "overflowX": "auto",  # setting to auto causes the dropdown-cell overlap bug
                    # "overflowY": "auto",  # setting to auto causes the dropdown-cell overlap bug
                    "padding-left": "1em",
                },
                style_header={
                    "backgroundColor": "black",
                    "color": "whitesmoke",
                    "whiteSpace": "normal",
                    "fontWeight": "normal",
                    "height": "auto",
                    "lineHeight": "11px",
                },
                style_cell={
                    "textAlign": "left",
                    "fontSize": 11,
                    "font-family": "sans-serif",
                    "padding-left": "0.5em",
                    # these widths will make it obvious if there's a new/extra column
                    "minWidth": "10px",
                    "width": "10px",
                    "maxWidth": "10px",
                },
                # style_cell_conditional set in callback
                style_data={
                    "whiteSpace": "normal",
                    "height": "auto",
                    "lineHeight": "12px",
                    "wordBreak": "normal",
                },
                # style_data_conditional set in callback
                # tooltip set in callback
                row_deletable=False,  # toggled in callback
                # hidden_columns set in callback
                page_size=0,  # 0 -> *HUGE* performance gains # toggled in callback
                # data set in callback
                # columns set in callback
                # dropdown set in callback
                # dropdown_conditional set in callback
                export_format="xlsx",
                export_headers="display",
                merge_duplicate_headers=True,
                # fixed_rows={"headers": True, "data": 0},
            ),
            #
            # Bottom Buttons
            du.fullscreen_loading(
                children=[
                    dbc.Row(
                        className="g-0 wbs-table-bottom-toolbar",  # "g-0" -> no gutters
                        children=[
                            #
                            # New Data
                            du.new_data_button(2),
                            #
                            # Show Totals
                            dbc.Button(
                                id="wbs-show-totals-button",
                                n_clicks=0,
                                className="table-tool-medium",
                            ),
                            #
                            # Show All Columns
                            dbc.Button(
                                id="wbs-show-all-columns-button",
                                n_clicks=0,
                                className="table-tool-medium",
                            ),
                            #
                            # Show All Rows
                            dbc.Button(
                                id="wbs-show-all-rows-button",
                                n_clicks=0,
                                className="table-tool-medium",
                            ),
                        ],
                    ),
                ]
            ),
            #
            # Table Autosaved
            du.make_timecheck_container("wbs-table-timecheck-container", loading=True),
            du.make_confirm_container("table", "Submit SOWs"),
            #
            html.Div(
                id="institution-values-below-table-container",
                hidden=True,
                children=[
                    #
                    # Computing Resources
                    html.H2(
                        className="section-header",
                        id="wbs-h2-inst-computing",
                        children="Computing Contributions",
                    ),
                    # Inputs
                    dbc.Row(
                        justify="center",
                        className="g-0",  # "g-0" -> no gutters
                        children=[
                            dbc.Col(
                                className="institution-headcount",
                                children=[
                                    html.Div(_label, className="caps"),
                                    dcc.Input(
                                        id=_id,
                                        className="institution-headcount-input",
                                        type="number",
                                        min=0,
                                        disabled=True,
                                    ),
                                ],
                            )
                            for _id, _label in [
                                ("wbs-cpus", "CPU"),
                                ("wbs-gpus", "GPU"),
                            ]
                        ],
                    ),
                    # Autosaved & Confirm
                    du.make_timecheck_container("wbs-computing-timecheck-container"),
                    du.make_confirm_container("computing", "Submit Counts"),
                    #
                    # Free Text & Autosaved
                    html.H2(
                        className="section-header",
                        id="wbs-h2-inst-textarea",
                        children="Miscellaneous Notes and Descriptions",
                    ),
                    dcc.Textarea(
                        id="wbs-textarea",
                        className="institution-text-area",
                        disabled=True,
                    ),
                    du.make_timecheck_container(
                        "wbs-institution-textarea-timecheck-container", loading=True
                    ),
                ],
            ),
            #
            # Admin Zone
            html.Div(
                id="wbs-admin-zone-div",
                hidden=True,
                className="d-grid gap-2 col-6 mx-auto",  # "col-6" -> width; "mx-auto" -> centered
                children=[
                    #
                    html.H2(className="section-header", children="Admin Zone"),
                    #
                    # Summary Table
                    du.fullscreen_loading(
                        children=[
                            html.Div(
                                style={
                                    "margin-right": "10rem",
                                    "width": "calc(100% - 10rem)",
                                },
                                children=[
                                    dbc.Button(
                                        id="wbs-summary-table-recalculate",
                                        n_clicks=0,
                                        children="Recalculate Institution Summary",
                                    ),
                                ],
                            ),
                            du.simple_table("wbs-summary-table"),
                        ]
                    ),
                    #
                    html.Hr(),
                    #
                    # Blame Table
                    du.fullscreen_loading(
                        children=[
                            html.Div(
                                style={
                                    "margin-right": "10rem",
                                    "width": "calc(100% - 10rem)",
                                },
                                children=[
                                    dbc.Button(
                                        id="wbs-blame-table-button",
                                        n_clicks=0,
                                        color=du.Color.DARK,
                                        children="View How SOWs Have Changed",
                                    ),
                                ],
                            ),
                            du.simple_table("wbs-blame-table"),
                        ],
                    ),
                    #
                    html.Hr(),
                    #
                    # Make Snapshot
                    dbc.Button(
                        "Make Collaboration-Wide Snapshot",
                        id="wbs-make-snapshot-button",
                        n_clicks=0,
                        color=du.Color.SUCCESS,
                        disabled=False,
                        style={"margin-bottom": "1rem"},
                    ),
                    #
                    html.Hr(),
                    #
                    # Reset Confirmations
                    dbc.Button(
                        "Reset Institution Confirmations",
                        id="wbs-reset-inst-confirmations-button",
                        n_clicks=0,
                        color=du.Color.SUCCESS,
                        disabled=False,
                        style={"margin-bottom": "1rem"},
                    ),
                    #
                    html.Hr(),
                    #
                    # Upload/Override XLSX
                    dbc.Button(
                        "Override All Institutions' SOW Tables with .xlsx",
                        id="wbs-upload-xlsx-launch-modal-button",
                        n_clicks=0,
                        color=du.Color.WARNING,
                        disabled=True,  # this isn't needed anymore
                        style={"margin-bottom": "1rem"},
                    ),
                ],
            ),
            #
            #
            #
            # Data Stores aka Cookies
            # - for fagging whether the institution values were changed
            dcc.Store(
                id="wbs-institution-values-first-time-flag",
                storage_type="memory",
                data=True,
            ),
            # - for storing the initial confirmation timestamps
            dcc.Store(id="wbs-headcounts-confirm-timestamp", storage_type="memory"),
            dcc.Store(id="wbs-table-confirm-timestamp", storage_type="memory"),
            dcc.Store(id="wbs-computing-confirm-timestamp", storage_type="memory"),
            # - for storing the last deleted record's id
            dcc.Store(id="wbs-last-deleted-record", storage_type="memory"),
            # - for discerning whether the table update was by the user vs automated
            # -- flags will agree only after table_data_exterior_controls() triggers table_data_interior_controls()
            dcc.Store(
                id="wbs-table-update-flag-exterior-control",
                storage_type="memory",
                data=False,
            ),
            dcc.Store(
                id="wbs-table-update-flag-interior-control",
                storage_type="memory",
                data=False,
            ),
            #
            # Container Divs -- for adding dynamic toasts, dialogs, etc.
            html.Div(id="wbs-toast-via-exterior-control-div"),
            html.Div(id="wbs-toast-via-confirm-deletion-div"),
            html.Div(id="wbs-toast-via-snapshot-div"),
            html.Div(id="wbs-toast-via-upload-div"),
            #
            # Modals & Toasts
            du.after_deletion_toast(),
            du.upload_modal(),
            du.upload_success_modal(),
            du.name_snapshot_modal(),
            # du.add_new_data_modal(),
            dcc.ConfirmDialog(id="wbs-confirm-deletion"),
            dbc.Button(
                id="wbs-undo-last-delete-hidden-button", style={"visibility": "hidden"}
            ),
            ###
        ]
    )
