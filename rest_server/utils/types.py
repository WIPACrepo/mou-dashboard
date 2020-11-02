"""Custom type definitions."""

from typing import Dict, List, Optional, TypedDict, Union

# Data Source types
DataEntry = Union[int, float, str]  # just data
Record = Dict[str, DataEntry]
Table = List[Record]


class SnapshotInfo(TypedDict):
    """The typed dict containing a snapshot's name, timestamp, and creator.

    Not a mongo schema. A subset of `SupplementalDoc` for REST calls.
    """

    timestamp: str
    name: str
    creator: str
    admin_only: bool


class InstitutionValues(TypedDict):
    """Values for an institution."""

    phds_authors: Optional[int]
    faculty: Optional[int]
    scientists_post_docs: Optional[int]
    grad_students: Optional[int]
    text: str


class SupplementalDoc(TypedDict):
    """Fields for an Supplemental document, which supplements a snapshot."""

    name: str
    timestamp: str
    creator: str
    snapshot_institution_values: Dict[str, InstitutionValues]
    admin_only: bool
