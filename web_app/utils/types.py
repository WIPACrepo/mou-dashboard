"""Custom type definitions."""


import dataclasses as dc
from typing import Collection, Dict, Final, List, Optional, Tuple

# Data Source types
StrNum = int | float | str  # just data
Record = Dict[str, StrNum]
Table = List[Record]


@dc.dataclass(frozen=True)
class SnapshotInfo:
    """The typed inst containing a snapshot's name, timestamp, and creator."""

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
TColumns = List[Dict[str, object]]  # columns
TSCCond = List[Dict[str, Collection[str]]]  # style_cell_conditional
TSDCond = List[Dict[str, Collection[str]]]  # style_data_conditional
TDDown = Dict[str, Dict[str, List[_StrDict]]]  # dropdown
TDDownCond = List[Dict[str, _StrDict | List[_StrDict]]]  # dropdown_conditional
TFocus = Dict[str, int] | None  # which cell to focus
TTooltips = Dict[str, Dict[str, DashVal]]


@dc.dataclass(frozen=True)
class InstitutionValues:
    """Values for an institution."""

    phds_authors: int | None
    faculty: int | None
    scientists_post_docs: int | None
    grad_students: int | None
    cpus: int | None
    gpus: int | None
    text: str
    headcounts_confirmed_ts: int  # timestamp
    table_confirmed_ts: int  # timestamp
    computing_confirmed_ts: int  # timestamp
