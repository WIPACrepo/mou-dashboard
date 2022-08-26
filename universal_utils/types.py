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
class InstitutionAttributeMetadata:
    """Metadata for an `InstitutionValues` attribute/attributes."""

    last_edit_ts: int = 0
    confirmation_ts: int = 0
    confirmation_touchstone_ts: int = 0

    def has_valid_confirmation(self) -> bool:
        """Return whether the confirmation is valid."""
        # using `>=` will pass the null-case where everything=0
        return (
            self.confirmation_ts >= self.last_edit_ts
            and self.confirmation_ts >= self.confirmation_touchstone_ts
        )


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
    headcounts_metadata: InstitutionAttributeMetadata
    table_metadata: InstitutionAttributeMetadata
    computing_metadata: InstitutionAttributeMetadata
