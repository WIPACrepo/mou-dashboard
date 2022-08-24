"""Custom type definitions."""

from typing import Collection, Dict, Final, List, Optional, Tuple

import universal_utils.types as uut

# Private
_StrDict = Dict[str, str]  # Ceci n'est pas une pipe


# Other Dash types
DashVal = Optional[uut.StrNum]  # dcc.Dropdown().value, dcc.Input().value
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
