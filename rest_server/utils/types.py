"""Custom type definitions."""

import dataclasses as dc

import universal_utils.types as uut
from bson.objectid import ObjectId
from typeguard import typechecked


@typechecked
@dc.dataclass(frozen=True)
class SupplementalDoc:
    """Fields for a Supplemental document, which supplements a snapshot."""

    name: str
    timestamp: str
    creator: str
    snapshot_institution_values: dict[str, uut.InstitutionValues]
    admin_only: bool
    _id: ObjectId | None = None
    confirmation_touchstone_ts: int = 0  # zero for legacy data

    def override_all_institutions_touchstones(self) -> None:
        """Override all institutions touchstones with internal value."""
        for inst_vals in self.snapshot_institution_values.values():
            #
            inst_vals.headcounts_metadata.override_touchstone(
                self.confirmation_touchstone_ts
            )
            #
            inst_vals.table_metadata.override_touchstone(
                self.confirmation_touchstone_ts
            )
            #
            inst_vals.computing_metadata.override_touchstone(
                self.confirmation_touchstone_ts
            )
