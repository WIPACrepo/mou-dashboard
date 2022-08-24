"""Custom type definitions."""

import dataclasses as dc
from typing import Dict, List

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


@dc.dataclass(frozen=True)
class SupplementalDoc:
    """Fields for an Supplemental document, which supplements a snapshot."""

    name: str
    timestamp: str
    creator: str
    snapshot_institution_values: Dict[str, InstitutionValues]
    admin_only: bool
    _id: ObjectId | None = None
