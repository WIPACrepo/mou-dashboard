"""Tab-toggled layout for a specified WBS."""


import dash_bootstrap_components as dbc  # type: ignore[import]
from dash import dash_table, dcc, html  # type: ignore[import]

from ..config import ENV
from ..utils import dash_utils as du


def layout() -> html.Div:
    """Construct the HTML."""
    return html.Div(
        children=[
            html.Div(id="dummy-input-for-setup", hidden=True),
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
            # Snapshot / Institution filter dropdown menu / Cloud Saved
            dbc.Row(
                className="g-0 bottom-border",  # "g-0" -> no gutters
                children=[
                    dbc.Col(
                        width=2,
                        children=[
                            du.ButtonIconLabelTooltipFactory.make(
                                "wbs-view-snapshots",
                                hidden=True,
                                icon_class=du.IconClassNames.CLOCK_ROTATE_LEFT,
                                label_text="View a Snapshot",
                                tooltip_text="click to select and view past statements of work",
                                width="17rem",
                                height="3.8rem",
                                border_width=0,
                                border_radius="0",
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
                                    searchable=True,
                                ),
                            ),
                            html.Div(
                                id="wbs-view-live-btn-div",
                                hidden=True,
                                # style={"margin-top": "0.25rem"},
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
                        className="institution-dropdown-container",
                        width=8,
                        children=[
                            dcc.Dropdown(
                                id="wbs-dropdown-institution",
                                className="institution-dropdown",
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
                        width=2,
                        children=du.ButtonIconLabelTooltipFactory.make(
                            "wbs-cloud-saved",
                            icon_class=du.IconClassNames.CLOUD,
                            label_text="Saved",
                            tooltip_text="your work is automatically being saved to the cloud",
                            float_right=True,
                            add_loading=True,
                            add_interval=True,
                            border_width=0,
                            width="17rem",
                            height="3.8rem",
                            border_radius="0",
                        ),
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
                        # className="g-0",  # "g-0" -> no gutters
                        children=[
                            du.make_stacked_label_component_float_left(
                                width=18,
                                label="PhDs & Authors",
                                component=dcc.Input(
                                    id="wbs-phds-authors",
                                    className="institution-headcount-input",
                                    type="number",
                                    min=0,
                                    disabled=True,
                                ),
                            ),
                            du.make_stacked_label_component_float_left(
                                width=18,
                                label="Faculty",
                                component=dcc.Input(
                                    id="wbs-faculty",
                                    className="institution-headcount-input",
                                    type="number",
                                    min=0,
                                    disabled=True,
                                ),
                            ),
                            du.make_stacked_label_component_float_left(
                                width=18,
                                label="Scientists/Post-Docs",
                                component=dcc.Input(
                                    id="wbs-scientists-post-docs",
                                    className="institution-headcount-input",
                                    type="number",
                                    min=0,
                                    disabled=True,
                                ),
                            ),
                            du.make_stacked_label_component_float_left(
                                width=18,
                                label="Graduate Students",
                                component=dcc.Input(
                                    id="wbs-grad-students",
                                    className="institution-headcount-input",
                                    type="number",
                                    min=0,
                                    disabled=True,
                                ),
                            ),
                            du.make_stacked_label_component_float_left(
                                width=15,
                                component=du.ButtonIconLabelTooltipFactory.make(
                                    "wbs-headcounts-confirm-yes",
                                    icon_class=du.IconClassNames.RIGHT_TO_BRACKET,  # set in callback
                                    label_text="Confirm",  # set in callback
                                    tooltip_text="headcounts need to be confirmed before each collaboration meeting",
                                    button_classname=du.ButtonIconLabelTooltipFactory.build_classname(
                                        outline=True,
                                        color=du.Color.SUCCESS,
                                    ),
                                    height="3.8rem",
                                ),
                            ),
                        ],
                    ),
                    # Autosaved & Confirm
                    # du.make_timecheck_container("wbs-headcounts-timecheck-container"),
                ],
            ),
            #
            html.H2(className="section-header", id="wbs-h2-sow-table"),
            #
            #
            dbc.Row(
                justify="center",
                className="g-0",  # "g-0" -> no gutters
                style={
                    "margin-left": "7rem",
                    # "margin-right": "1rem",
                    "margin-bottom": "4rem",
                    # "text-align": "right",
                },
                children=[
                    dbc.Col(
                        width=2,
                        style={"font-size": "10px"},
                        children=[
                            dbc.Label("AD – Administration"),
                            dbc.Label("KE – Key Personnel (Faculty)"),
                        ],
                    ),
                    dbc.Col(
                        width=2,
                        style={"font-size": "10px"},
                        children=[
                            dbc.Label("CS – Computer Science"),
                            dbc.Label("MA – Manager"),
                        ],
                    ),
                    dbc.Col(
                        width=2,
                        style={"font-size": "10px"},
                        children=[
                            dbc.Label("DS – Data Science"),
                            dbc.Label("PO – Postdoctoral Associates"),
                        ],
                    ),
                    dbc.Col(
                        width=2,
                        style={"font-size": "10px"},
                        children=[
                            dbc.Label("EN – Engineering"),
                            dbc.Label("SC – Scientist"),
                        ],
                    ),
                    dbc.Col(
                        width=2,
                        style={"font-size": "10px"},
                        children=[
                            dbc.Label("GR – Graduate (PhD) Students"),
                            dbc.Label("WO – Winterover"),
                        ],
                    ),
                    dbc.Col(
                        width=2,
                        style={"font-size": "10px"},
                        children=[
                            dbc.Label("IT – Information Technology"),
                        ],
                    ),
                ],
            ),
            #
            # Top Tools
            dbc.Row(
                style={"padding-left": "1em", "padding-right": "120px"},
                children=[
                    # Add Button
                    dbc.Col(
                        width=3,
                        children=du.ButtonIconLabelTooltipFactory.make(
                            "wbs-new-data-button",
                            icon_class=du.IconClassNames.PEN_TO_SQUARE,
                            label_text="Create New Statement of Work",
                            tooltip_text="click to add a new statement of work",
                            button_classname=du.ButtonIconLabelTooltipFactory.build_classname(
                                outline=True,
                                color=du.Color.DARK,
                            ),
                            height="25.53px",
                        ),
                    ),
                    # Confirm Table
                    dbc.Col(
                        width=3,
                        children=du.ButtonIconLabelTooltipFactory.make(
                            "wbs-table-confirm-yes",
                            icon_class=du.IconClassNames.RIGHT_TO_BRACKET,  # set in callback
                            label_text="Confirm All Statements of Work",  # set in callback
                            tooltip_text="SOWs need to be confirmed before each collaboration meeting",
                            button_classname=du.ButtonIconLabelTooltipFactory.build_classname(
                                outline=True,
                                color=du.Color.SUCCESS,
                            ),
                            height="25.53px",
                            hidden=True,
                        ),
                    ),
                    # # Labor Category filter dropdown menu
                    # dbc.Col(
                    #     width=2,
                    #     children=html.Div(
                    #         id="wbs-filter-labor-container",
                    #         hidden=True,
                    #         children=dcc.Dropdown(
                    #             id="wbs-filter-labor",
                    #             placeholder="Filter by Labor Category",
                    #             className="table-custom-filter caps",
                    #             # options set in callback
                    #             # value set in callback
                    #             optionHeight=30,
                    #         ),
                    #     ),
                    # ),
                    #
                    # New Data
                    # du.new_data_button(2),
                    #
                    # Show Totals
                    # dbc.Button(
                    #     id="wbs-show-totals-button",
                    #     n_clicks=0,
                    #     className="table-tool-medium",
                    #     children="Totals",
                    # ),
                    dbc.Col(
                        width=2,
                        children=du.ButtonIconLabelTooltipFactory.make(
                            "wbs-show-totals-button",
                            icon_class=du.IconClassNames.PLUS_MINUS,  # set in callback
                            label_text="Totals",
                            height="25.53px",
                            add_loading=True,
                            width="100%",
                        ),
                    ),
                    #
                    # Show All Columns
                    # dbc.Button(
                    #     id="wbs-show-all-columns-button",
                    #     n_clicks=0,
                    #     className="table-tool-medium",
                    #     children="All Columns",
                    # ),
                    dbc.Col(
                        width=2,
                        children=du.ButtonIconLabelTooltipFactory.make(
                            "wbs-show-all-columns-button",
                            icon_class=du.IconClassNames.EXPAND,  # set in callback
                            label_text="All Columns",
                            height="25.53px",
                            add_loading=True,
                            width="100%",
                        ),
                    ),
                    #
                    # Show Pages
                    dbc.Col(
                        width=2,
                        children=du.ButtonIconLabelTooltipFactory.make(
                            "wbs-show-all-rows-button",
                            icon_class=du.IconClassNames.LAYER_GROUP,  # set in callback
                            label_text="Show Pages",
                            height="25.53px",
                            hidden=True,  # set in callback
                            add_loading=True,
                            width="100%",
                        ),
                    ),
                ],
            ),
            #
            # Table
            html.Div(
                id="wbs-data-table-container",
                className="data-table-outer",
                children=dash_table.DataTable(
                    id="wbs-data-table",
                    editable=False,
                    sort_mode="multi",
                    filter_action="native",
                    filter_options={"case": "insensitive"},
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
            ),
            #
            # Bottom Buttons
            # html.Div(
            #     id="wbs-table-bottom-toolbar-container",
            #     hidden=True,
            #     children=du.fullscreen_loading(
            #         children=[
            #             dbc.Row(
            #                 id="wbs-table-bottom-toolbar",
            #                 className="g-0 wbs-table-bottom-toolbar",  # "g-0" -> no gutters
            #                 # style={}, # updated by callback
            #                 children=[
            #                 ],
            #             ),
            #         ],
            #     ),
            # ),
            #
            # Table Autosaved
            # du.make_timecheck_container("wbs-table-timecheck-container", loading=True),
            # du.make_confirm_container("table", ""),
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
                        # className="g-0",  # "g-0" -> no gutters
                        children=[
                            du.make_stacked_label_component_float_left(
                                width=15,
                                label="Number of CPUs",
                                component=dcc.Input(
                                    id="wbs-cpus",
                                    className="institution-headcount-input",
                                    type="number",
                                    min=0,
                                    disabled=True,
                                ),
                            ),
                            du.make_stacked_label_component_float_left(
                                width=15,
                                label="Number of GPUs",
                                component=dcc.Input(
                                    id="wbs-gpus",
                                    className="institution-headcount-input",
                                    type="number",
                                    min=0,
                                    disabled=True,
                                ),
                            ),
                            du.make_stacked_label_component_float_left(
                                width=15,
                                component=du.ButtonIconLabelTooltipFactory.make(
                                    "wbs-computing-confirm-yes",
                                    icon_class=du.IconClassNames.RIGHT_TO_BRACKET,  # set in callback
                                    label_text="Confirm",  # set in callback
                                    tooltip_text="computing contributions need to be confirmed before each collaboration meeting",
                                    button_classname=du.ButtonIconLabelTooltipFactory.build_classname(
                                        outline=True,
                                        color=du.Color.SUCCESS,
                                    ),
                                    height="3.8rem",
                                ),
                            ),
                        ],
                    ),
                    # Autosaved & Confirm
                    # du.make_timecheck_container("wbs-computing-timecheck-container"),
                    # du.make_confirm_container("computing", "Submit Counts"),
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
                    # du.make_timecheck_container(
                    #     "wbs-institution-textarea-timecheck-container", loading=True
                    # ),
                ],
            ),
            #
            # Admin Zone
            html.Div(
                id="wbs-admin-zone-div",
                hidden=True,
                className="d-grid gap-2 mx-auto",  # "col-#" -> width; "mx-auto" -> centered
                children=[
                    #
                    html.H2(className="section-header", children="Admin Zone"),
                    #
                    # Summary Table
                    du.fullscreen_loading(
                        children=[
                            html.Div(
                                className="admin-table-button",
                                children=[
                                    dbc.Button(
                                        id="wbs-summary-table-recalculate",
                                        n_clicks=0,
                                        color=du.Color.SECONDARY,
                                        children="Recalculate Institution Summary",
                                        style={"width": "100%"},
                                    ),
                                ],
                            ),
                            html.Div(
                                className="admin-table",
                                children=du.simple_table("wbs-summary-table"),
                            ),
                        ]
                    ),
                    #
                    html.Hr(),
                    #
                    # Blame Table
                    du.fullscreen_loading(
                        children=[
                            html.Div(
                                className="admin-table-button",
                                children=[
                                    dbc.Button(
                                        id="wbs-blame-table-button",
                                        n_clicks=0,
                                        color=du.Color.DARK,
                                        children="View How SOWs Have Changed",
                                        style={"width": "100%"},
                                    ),
                                ],
                            ),
                            html.Div(
                                className="admin-table",
                                children=du.simple_table("wbs-blame-table"),
                            ),
                        ],
                    ),
                    #
                    html.Hr(),
                    dbc.Row(
                        children=[
                            # Make Snapshot
                            dbc.Col(
                                width=4,
                                children=dbc.Button(
                                    "Make Collaboration-Wide Snapshot",
                                    id="wbs-make-snapshot-button",
                                    n_clicks=0,
                                    color=du.Color.SUCCESS,
                                    disabled=False,
                                    style={"width": "100%"},
                                ),
                            ),
                            # Reset Confirmations
                            dbc.Col(
                                width=4,
                                children=dbc.Button(
                                    "Reset Institution Confirmations",
                                    id="wbs-retouchstone-button",
                                    n_clicks=0,
                                    color=du.Color.WARNING,
                                    disabled=False,
                                    style={"width": "100%"},
                                ),
                            ),
                            # Upload/Override XLSX
                            dbc.Col(
                                width=4,
                                children=dbc.Button(
                                    "Override All Institutions' Statements of Work with .xlsx",
                                    id="wbs-upload-xlsx-launch-modal-button",
                                    n_clicks=0,
                                    color=du.Color.DANGER,
                                    disabled=not ENV.DEBUG,  # only for local testing
                                    style={"width": "100%"},
                                ),
                            ),
                        ]
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
            # dcc.Store(id="wbs-headcounts-confirm-timestamp", storage_type="memory"),
            # dcc.Store(id="wbs-table-confirm-timestamp", storage_type="memory"),
            # dcc.Store(id="wbs-computing-confirm-timestamp", storage_type="memory"),
            # - for storing confirmation info
            dcc.Store(id="wbs-store-confirm-headcounts", storage_type="memory"),
            dcc.Store(id="wbs-store-confirm-table", storage_type="memory"),
            dcc.Store(id="wbs-store-confirm-computing", storage_type="memory"),
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
            # Intervals
            dcc.Interval(
                id="wbs-interval-trigger-confirmation-refreshes",
                interval=10 * 1000 if ENV.DEBUG else 30 * 1000,
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
