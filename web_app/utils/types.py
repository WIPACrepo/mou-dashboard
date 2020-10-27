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


class InstitutionValues(TypedDict):
    """Values for an institution."""

    phds_authors: int
    faculty: int
    scientists_post_docs: int
    grad_students: int
    text: str


# Private
_StrDict = Dict[str, str]  # Ceci n'est pas une pipe


# Dash DataTable Property types
# NOTE: data is Table type
TColumns = List[_StrDict]  # columns
TSDCond = List[Dict[str, Collection[str]]]  # style_data_conditional
TDDown = Dict[str, Dict[str, List[_StrDict]]]  # dropdown
TDDownCond = List[Dict[str, Union[_StrDict, List[_StrDict]]]]  # dropdown_conditional
TFocus = Optional[Dict[str, int]]  # which cell to focus

# Other Dash types
DDValue = Optional[StrNum]  # dcc.Dropdown().value
DDValue_types: Final[Tuple[type, ...]] = (str, int, float, type(None))  # for runtime
assert set(DDValue.__dict__["__args__"]) == set(DDValue_types)
