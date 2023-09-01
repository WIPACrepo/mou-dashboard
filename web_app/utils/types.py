"""Custom type definitions."""

from typing import Collection, Final, Optional

import universal_utils.types as uut

# Private
_StrDict = dict[str, str]  # Ceci n'est pas une pipe


# Other Dash types
DashVal = Optional[uut.StrNum]  # dcc.Dropdown().value, dcc.Input().value
DashVal_types: Final[tuple[type, ...]] = (str, int, float, type(None))  # for runtime
assert set(DashVal.__dict__["__args__"]) == set(DashVal_types)


# Dash DataTable Property types
# NOTE: data is Table type
TColumns = list[dict[str, object]]  # columns
TSCCond = list[dict[str, Collection[str]]]  # style_cell_conditional
TSDCond = list[dict[str, Collection[str]]]  # style_data_conditional
TDDown = dict[str, dict[str, list[_StrDict]]]  # dropdown
TDDownCond = list[dict[str, _StrDict | list[_StrDict]]]  # dropdown_conditional
TFocus = dict[str, int] | None  # which cell to focus
TTooltips = dict[str, dict[str, DashVal]]
