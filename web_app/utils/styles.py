"""Common HTML styles."""

HIDDEN = {"visibility": "hidden"}

CENTERED_100 = {
    "width": "100%",
    "display": "flex",
    "align-items": "center",
    "justify-content": "center",
}

WIDTH_45 = {"width": "45%"}

LEFT_45 = {"width": "45%", "float": "left"}

WIDTH_30 = {
    "width": "30%",
}

CENTERED_30 = {
    "width": "30%",
    "display": "flex",
    "align-items": "center",
    "justify-content": "center",
}

CONTENT_STYLE = {
    "border-left": "1px #d6d6d6 solid",
    "border-right": "1px #d6d6d6 solid",
    "padding-top": "2%",
    "padding-left": "2%",
    "padding-right": "2%",
}

# Hr

SHORT_HR = {"margin-left": "15%", "margin-right": "15%"}

# Stats

STAT_NUMBER = {
    "font-family": "monospace",
    "fontSize": 25,
    "text-align": "right",
    "display": "inline-block",
    "padding-right": "4%",
}

STAT_LABEL = {"fontSize": 20, "display": "inline-block"}

# Styles for Tabs

_TAB_HEIGHT = "5vh"

TAB_SELECTED_STYLE = {"padding": "0", "line-height": _TAB_HEIGHT}

TAB_STYLE = {"padding": "0", "line-height": _TAB_HEIGHT}

TABS_STYLE = {"height": _TAB_HEIGHT, "font-size": "120%"}
