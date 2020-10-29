"""Custom type definitions."""


from typing import Collection, Dict, Final, List, Optional, Tuple, TypedDict, Union

# Data Source types
StrNum = Union[int, float, str]  # just data
Record = Dict[str, StrNum]
Table = List[Record]


class SnapshotInfo(TypedDict):
    """The typed dict containing a snapshot's name, timestamp, and creator."""

    timestamp: str
    name: str
    creator: str


# Private
_StrDict = Dict[str, str]  # Ceci n'est pas une pipe


# Other Dash types
DashVal = Optional[StrNum]  # dcc.Dropdown().value, dcc.Input().value
DashVal_types: Final[Tuple[type, ...]] = (str, int, float, type(None))  # for runtime
assert set(DashVal.__dict__["__args__"]) == set(DashVal_types)


# Dash DataTable Property types
# NOTE: data is Table type
TColumns = List[_StrDict]  # columns
TSCCond = List[Dict[str, Collection[str]]]  # style_cell_conditional
TSDCond = List[Dict[str, Collection[str]]]  # style_data_conditional
TDDown = Dict[str, Dict[str, List[_StrDict]]]  # dropdown
TDDownCond = List[Dict[str, Union[_StrDict, List[_StrDict]]]]  # dropdown_conditional
TFocus = Optional[Dict[str, int]]  # which cell to focus
TTooltips = Dict[str, Dict[str, DashVal]]
