"""Custom type definitions."""

import dataclasses as dc
import time

from bson.objectid import ObjectId

# Data Source types
# for web
StrNum = int | float | str  # just data
WebRecord = dict[str, StrNum]
WebTable = list[WebRecord]
# for db
DataEntry = StrNum | ObjectId  # just data + mongo ID
DBRecord = dict[str, DataEntry]
DBTable = list[DBRecord]


@dc.dataclass(frozen=True)
class SnapshotInfo:
    """The typed dict containing a snapshot's name, timestamp, and creator.

    Not a mongo schema. A subset of `SupplementalDoc` for REST calls.
    """

    timestamp: str
    name: str
    creator: str
    admin_only: bool


EXPIRED = "expired"
CHANGES = "changes"
GOOD = "good"


@dc.dataclass(frozen=True)
class InstitutionAttrMetadata:
    """Metadata for an `InstitutionValues` attribute/attributes."""

    last_edit_ts: int = 0
    confirmation_ts: int = 0
    confirmation_touchstone_ts: int = 0

    def has_valid_confirmation(self) -> bool:
        """Return whether the confirmation is valid."""
        # using `>=` will pass the null-case where everything=0
        return not self._is_expired() and not self._has_new_changes()

    def _is_expired(self) -> bool:
        return self.confirmation_ts < self.confirmation_touchstone_ts

    def _has_new_changes(self) -> bool:
        return self.confirmation_ts < self.last_edit_ts

    def get_confirmation_reason(self) -> str:
        """Get a human-readable reason for why the confirmation is
        valid/invalid."""
        if self._has_new_changes():
            return CHANGES
        if self._is_expired():
            return EXPIRED
        return GOOD


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
    headcounts_metadata: InstitutionAttrMetadata = InstitutionAttrMetadata()
    table_metadata: InstitutionAttrMetadata = InstitutionAttrMetadata()
    computing_metadata: InstitutionAttrMetadata = InstitutionAttrMetadata()

    def compute_last_edits(
        self,
        phds_authors: int | None,
        faculty: int | None,
        scientists_post_docs: int | None,
        grad_students: int | None,
        cpus: int | None,
        gpus: int | None,
        text: str,
    ) -> "InstitutionValues":
        """Copy fields from args and compute new metadata.

        Non-table metadata's `last_edit_ts` values are computed by
        diffing with `self`.
        """
        now = int(time.time())

        # Update "last edit"?
        if (
            self.phds_authors != phds_authors
            or self.faculty != faculty
            or self.scientists_post_docs != scientists_post_docs
            or self.grad_students != grad_students
        ):
            headcounts_metadata = dc.replace(self.headcounts_metadata, last_edit_ts=now)
        else:
            headcounts_metadata = self.headcounts_metadata

        # Update "last edit"?
        if self.cpus != cpus or self.gpus != gpus:
            computing_metadata = dc.replace(self.computing_metadata, last_edit_ts=now)
        else:
            computing_metadata = self.computing_metadata

        return InstitutionValues(
            phds_authors=phds_authors,
            faculty=faculty,
            scientists_post_docs=scientists_post_docs,
            grad_students=grad_students,
            cpus=cpus,
            gpus=gpus,
            text=text,
            headcounts_metadata=headcounts_metadata,
            table_metadata=self.table_metadata,  # table values live elsewhere
            computing_metadata=computing_metadata,
        )

    def restful_dict(self, institution: str) -> dict[str, int | str | None]:
        """Get a dict w/o the metadata fields + institution."""
        dicto = dc.asdict(self)
        dicto.pop("headcounts_metadata")
        dicto.pop("table_metadata")
        dicto.pop("computing_metadata")
        dicto["institution"] = institution

        for key in list(dicto.keys()):
            if dicto[key] is None:
                del dicto[key]

        return dicto

    def confirm(
        self, headcounts: bool, table: bool, computing: bool
    ) -> "InstitutionValues":
        """Confirm the indicated values (update their metadata's
        `confirmation_ts`)."""
        now = int(time.time())

        headcounts_metadata = self.headcounts_metadata
        if headcounts:
            headcounts_metadata = dc.replace(
                self.headcounts_metadata, confirmation_ts=now
            )

        table_metadata = self.table_metadata
        if table:
            table_metadata = dc.replace(self.table_metadata, confirmation_ts=now)

        computing_metadata = self.computing_metadata
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
