"""Custom type definitions."""


from typing import Collection, Dict, List, Union

# Data types
DataEntry = Union[int, float, str]  # just data
Record = Dict[str, DataEntry]
Table = List[Record]

# Private
_StrDict = Dict[str, str]  # Ceci n'est pas une pipe


# Dash DataTable properties
TData = List[Dict[str, DataEntry]]  # data
SDCond = List[Dict[str, Collection[str]]]  # style_data_conditional
DDown = Dict[str, Dict[str, List[_StrDict]]]  # dropdown
DDCond = List[Dict[str, Union[_StrDict, List[_StrDict]]]]  # dropdown_conditional
