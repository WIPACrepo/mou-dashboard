"""Custom type definitions."""

import dataclasses as dc
from typing import Dict, List

from bson.objectid import ObjectId

# Data Source types
# for web
StrNum = int | float | str  # just data
WebRecord = Dict[str, StrNum]
WebTable = List[WebRecord]
# for db
DataEntry = StrNum | ObjectId  # just data + mongo ID
DBRecord = Dict[str, DataEntry]
DBTable = List[DBRecord]


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
