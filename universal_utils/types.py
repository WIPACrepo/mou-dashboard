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
class InstitutionAttrMetadata:
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

    phds_authors: int | None = None
    faculty: int | None = None
    scientists_post_docs: int | None = None
    grad_students: int | None = None
    cpus: int | None = None
    gpus: int | None = None
    text: str = ""
    headcounts_metadata: InstitutionAttrMetadata | None = InstitutionAttrMetadata()
    table_metadata: InstitutionAttrMetadata | None = InstitutionAttrMetadata()
    computing_metadata: InstitutionAttrMetadata | None = InstitutionAttrMetadata()

    def no_metadata_check(self) -> None:
        """Raise a ValueError if one (or more) of the metadata fields is not None."""
        if (
            self.headcounts_metadata is not None
            or self.table_metadata is not None
            or self.computing_metadata is not None
        ):
            raise ValueError(f"Instance has non-None metadata field(s): {self}")

    def update_anew(self, newer: "InstitutionValues") -> "InstitutionValues":
        """Copy non-metadata fields from `newer` and compute new metadata.

        Non-table metadata's `last_edit_ts` values are computed by diffing with `self`.

        `newer` cannot have any non-None metadata fields (simplifies assumptions).
        """
        newer.no_metadata_check()

        now = int(time.time())

        # Update "last edit"?
        if (
            self.phds_authors != newer.phds_authors
            or self.faculty != newer.faculty
            or self.scientists_post_docs != newer.scientists_post_docs
            or self.grad_students != newer.grad_students
        ):
            headcounts_metadata = dc.replace(self.headcounts_metadata, last_edit_ts=now)
        else:
            headcounts_metadata = self.headcounts_metadata

        # Update "last edit"?
        if self.cpus != newer.cpus or self.gpus != newer.gpus:
            computing_metadata = dc.replace(self.computing_metadata, last_edit_ts=now)
        else:
            computing_metadata = self.computing_metadata

        return dc.replace(
            newer,
            headcounts_metadata=headcounts_metadata,
            computing_metadata=computing_metadata,
        )

    def without_metadatas(self) -> "InstitutionValues":
        """Get an instance w/o the metadata fields."""
        return dc.replace(
            self,
            headcounts_metadata=None,
            table_metadata=None,
            computing_metadata=None,
        )

    def confirm(
        self, headcounts: bool, table: bool, computing: bool
    ) -> "InstitutionValues":
        """Confirm the indicated values (update their metadata's `confirmation_ts`)."""
        now = int(time.time())

        if headcounts:
            headcounts_metadata = dc.replace(
                self.headcounts_metadata, confirmation_ts=now
            )

        if table:
            table_metadata = dc.replace(self.table_metadata, confirmation_ts=now)

        if computing:
            computing_metadata = dc.replace(
                self.computing_metadata, confirmation_ts=now
            )

        return dc.replace(
            self,
            headcounts_metadata=headcounts_metadata,
            table_metadata=table_metadata,
            computing_metadata=computing_metadata,
        )
