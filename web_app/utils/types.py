"""Custom type definitions."""


from typing import Collection, Dict, List, Optional, Union

# Data Source types
DataEntry = Union[int, float, str]  # just data
Record = Dict[str, DataEntry]
Table = List[Record]

# Private
_StrDict = Dict[str, str]  # Ceci n'est pas une pipe


# Dash DataTable Property types
# NOTE: data is Table type
TColumns = List[_StrDict]  # columns
TSDCond = List[Dict[str, Collection[str]]]  # style_data_conditional
TDDown = Dict[str, Dict[str, List[_StrDict]]]  # dropdown
TDDownCond = List[Dict[str, Union[_StrDict, List[_StrDict]]]]  # dropdown_conditional
TFocus = Optional[Dict[str, int]]  # which cell to focus
