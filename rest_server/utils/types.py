"""Custom type definitions."""

from typing import Dict, List, TypedDict, Union

# Data Source types
DataEntry = Union[int, float, str]  # just data
Record = Dict[str, DataEntry]
Table = List[Record]


class SnapshotPair(TypedDict):
    """The typed dict containing a snapshot's name and timestamp."""

    timestamp: str
    name: str
    creator: str


class InstitutionValues(TypedDict):
    """Values for an institution."""

    text: str
    phds_authors: int
    scientists_postdocs: int
    grad_students: int


class SupplementalDoc(TypedDict):
    """Fields for an Supplemental document."""

    name: str
    timestamp: str
    creator: str
    snapshot_institution_values: Dict[str, InstitutionValues]
