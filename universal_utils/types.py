"""Custom type definitions."""

import dataclasses as dc
import time
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

    def update_anew(self, newer: "InstitutionValues") -> "InstitutionValues":
        """Copy all fields from `newer`, and update all metadata `last_edit_ts` values by diffing with `self`."""

        # Update "last edit"?
        if (
            self.phds_authors != newer.phds_authors
            or self.faculty != newer.faculty
            or self.scientists_post_docs != newer.scientists_post_docs
            or self.grad_students != newer.grad_students
        ):
            headcounts_metadata = dc.replace(
                newer.headcounts_metadata, last_edit_ts=int(time.time())
            )
        else:
            headcounts_metadata = newer.headcounts_metadata

        # Update "last edit"?
        if False:  # TODO
            table_metadata = dc.replace(
                newer.table_metadata, last_edit_ts=int(time.time())
            )
        else:
            table_metadata = newer.table_metadata

        # Update "last edit"?
        if self.cpus != newer.cpus or self.gpus != newer.gpus:
            computing_metadata = dc.replace(
                newer.computing_metadata, last_edit_ts=int(time.time())
            )
        else:
            computing_metadata = newer.computing_metadata

        return InstitutionValues(
            newer.phds_authors,
            newer.faculty,
            newer.scientists_post_docs,
            newer.grad_students,
            newer.cpus,
            newer.gpus,
            newer.text,
            headcounts_metadata=headcounts_metadata,
            table_metadata=table_metadata,
            computing_metadata=computing_metadata,
        )
