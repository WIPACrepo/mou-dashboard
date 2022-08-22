"""Custom type definitions."""

import dataclasses as dc
from typing import Dict, List, Optional

from bson.objectid import ObjectId

# Data Source types
DataEntry = int | float | str | ObjectId  # just data
Record = Dict[str, DataEntry]
Table = List[Record]


@dc.dataclass(frozen=True)
class SnapshotInfo:
    """The typed dict containing a snapshot's name, timestamp, and creator.

    Not a mongo schema. A subset of `SupplementalDoc` for REST calls.
    """

    timestamp: str
    name: str
    creator: str
    admin_only: bool


@dc.dataclass(frozen=True)
class InstitutionValues:
    """Values for an institution."""

    phds_authors: Optional[int]
    faculty: Optional[int]
    scientists_post_docs: Optional[int]
    grad_students: Optional[int]
    cpus: Optional[int]
    gpus: Optional[int]
    text: str
    headcounts_confirmed: bool
    computing_confirmed: bool


@dc.dataclass(frozen=True)
class SupplementalDoc:
    """Fields for an Supplemental document, which supplements a snapshot."""

    name: str
    timestamp: str
    creator: str
    snapshot_institution_values: Dict[str, InstitutionValues]
    admin_only: bool
    _id: Optional[ObjectId] = None
