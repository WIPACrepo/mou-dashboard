"""Interface with Smartsheet API."""

import dash  # type: ignore[import]
import dash_table  # type: ignore[import]
import numpy as np  # type: ignore[import]
import pandas as pd  # type: ignore[import]
import smartsheet  # type: ignore[import]

with open("smartsheet.key", "r") as f:
    ACCESS_TOKEN = f.readline()

SHEET_ID = "671120501303172"


# SMARTSHEET -------------------------------------------------------

# client initialization
print("Initialize client")
smartsheet_client = smartsheet.Smartsheet(ACCESS_TOKEN)
# make sure not to miss any error
smartsheet_client.errors_as_exceptions(True)

print("Access Smartsheet")
sheet = smartsheet_client.Sheets.get_sheet(SHEET_ID)  # 'Copy of M&O Open Tasks'

# Get all columns.
action = smartsheet_client.Sheets.get_columns(SHEET_ID, include_all=True)
columns = action.data

# For each column, print Id and Title.
cstring = []
for col in columns:
    cstring.append(col.title)
# print(cstring)

# Get rows
sheet = smartsheet_client.Sheets.get_sheet(SHEET_ID)

rlstring = []
for row in sheet.rows:
    rstring = []
    for c in range(0, len(sheet.columns)):
        rstring.append(row.cells[c].value)
    rlstring.append(rstring)
#    print(rlstring)


# DASH -------------------------------------------------------------
# Read DataFrame from SmartSheet data
df = pd.DataFrame(np.array(rlstring), columns=cstring)
# df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')

print("Initialize dash object")
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# print('Build html object')
# app.layout = html.Div(children=[
#    html.H1(children='IceCube MoU'),
#    html.Div(children='''Statement of Work'''),
#    html.H2(id='example-graph',children="Loaded %d rows from sheet: %s" % (len(sheet.rows), sheet.name))
# ])

print("Build HTML Table")
app.layout = dash_table.DataTable(
    editable=True,
    id="Table",
    columns=[{"name": i, "id": i} for i in df.columns],
    data=df.to_dict("records"),
)


#    html.Table(
#        [
#            html.Tr([html.Th(c) for c in cstring]),
#            html.Tr([html.Td(c) for c in rstring]),
#        ]
#    )

if __name__ == "__main__":
    app.run_server(debug=True)
