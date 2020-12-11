"""Tab-toggled layout for a specified WBS."""


import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore[import]
import dash_html_components as html  # type: ignore[import]
import dash_table  # type: ignore[import]

from ..data_source import table_config as tc
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
                    dbc.Button(
                        "View Today's SOW",
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
                    "margin-bottom": "2rem",
                },
                className="caps",
                color=du.Color.LIGHT,
                is_open=False,
            ),
            #
            # Load Snapshots
            html.Div(
                className="large-dropdown-container",
                children=[
                    dcc.Dropdown(
                        id="wbs-current-snapshot-ts",
                        className="large-dropdown snapshot-dropdown",
                        placeholder="...",  # set in callback
                        value="",
                        disabled=False,
                        persistence=True,
                        searchable=False,
                    ),
                ],
            ),
            html.Div(
                "click above to select and view past statements of work",
                style={
                    "font-style": "italic",
                    "text-align": "center",
                    "height": "1.5rem",
                    "line-height": "1.5rem",
                    "color": "gray",
                },
            ),
            #
            html.H2(className="section-header", children="Institution"),
            #
            # Institution filter dropdown menu
            html.Div(
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
                    #
                    dbc.Row(
                        justify="center",
                        no_gutters=True,
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
                                ("wbs-scientists-post-docs", "Scientists/Post-Docs",),
                                ("wbs-grad-students", "Grad Students"),
                            ]
                        ],
                    ),
                    #
                    dcc.Loading(
                        type="default",
                        color=du.TEAL,
                        children=[
                            html.Div(
                                className="last-updated-label caps",
                                id="wbs-institution-values-last-updated-label",
                            ),
                        ],
                    ),
                ],
            ),
            #
            html.H2(className="section-header", id="wbs-h2-sow-table"),
            #
            # Top Tools
            dbc.Row(
                className="wbs-table-top-toolbar",
                no_gutters=True,
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
                # style_cell_conditional set in callback
                style_data={
                    "whiteSpace": "normal",
                    "height": "auto",
                    "lineHeight": "20px",
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
                        className="wbs-table-bottom-toolbar",
                        no_gutters=True,
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
            # Last Refreshed
            dcc.Loading(
                type="default",
                color=du.TEAL,
                children=[
                    html.Label(
                        id="wbs-table-last-updated-label",
                        className="last-updated-label caps",
                    )
                ],
            ),
            #
            # Free Text
            html.Div(
                id="institution-textarea-container",
                hidden=True,
                children=[
                    html.H2(
                        className="section-header",
                        id="wbs-h2-inst-textarea",
                        children="Notes and Descriptions",
                    ),
                    dcc.Textarea(
                        id="wbs-textarea",
                        className="institution-text-area",
                        disabled=True,
                    ),
                    html.Div(
                        className="last-updated-label caps",
                        id="wbs-institution-textarea-last-updated-label",
                    ),
                ],
            ),
            #
            # Admin Zone
            html.Div(
                id="wbs-admin-zone-div",
                hidden=True,
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
                                        block=True,
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
                                        block=True,
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
                        block=True,
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
                        block=True,
                        n_clicks=0,
                        color=du.Color.WARNING,
                        disabled=False,
                        style={"margin-bottom": "1rem"},
                    ),
                ],
            ),
            #
            #
            #
            # Data Stores aka Cookies
            # - for caching the table config, to limit REST calls
            dcc.Store(
                id="wbs-table-config-cache",
                storage_type="memory",
                data=tc.TableConfigParser.get_configs(),  # get all tables' configs
            ),
            # - for fagging whether the institution values were changed
            dcc.Store(
                id="wbs-institution-values-first-time-flag",
                storage_type="memory",
                data=True,
            ),
            # - for storing the last deleted record's id
            dcc.Store(id="wbs-last-deleted-id", storage_type="memory"),
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
            html.Div(id="wbs-toast-via-interior-control-div"),
            html.Div(id="wbs-toast-via-snapshot-div"),
            html.Div(id="wbs-toast-via-upload-div"),
            #
            # Modals & Toasts
            du.deletion_toast(),
            du.upload_modal(),
            du.upload_success_modal(),
            du.name_snapshot_modal(),
            du.add_new_data_modal(),
            ###
        ]
    )
