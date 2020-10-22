"""Tab-toggled layout for a specified WBS."""


import dash_bootstrap_components as dbc  # type: ignore[import]
import dash_core_components as dcc  # type: ignore[import]
import dash_html_components as html  # type: ignore[import]
import dash_table  # type: ignore[import]

from ..data_source import table_config as tc
from ..utils import dash_utils as du


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
            #
            html.Div(
                id="wbs-admin-zone-div",
                children=[
                    html.Hr(),
                    # Upload/Override XLSX
                    dbc.Button(
                        "Override Live Table with .xlsx",
                        id="wbs-upload-xlsx-launch-modal-button",
                        block=True,
                        n_clicks=0,
                        color=du.Color.WARNING,
                        disabled=False,
                        style={"margin-bottom": "1rem"},
                    ),
                    html.Hr(),
                    # Summary Table
                    dbc.Button(id="wbs-summary-table-recalculate", n_clicks=0),
                    dash_table.DataTable(id="wbs-summary-table", editable=False),
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
