"""Custom type definitions."""

import dataclasses as dc
from typing import Any

import dacite
import universal_utils.types as uut
from bson.objectid import ObjectId


@dc.dataclass(frozen=True)
class SupplementalDoc:
    """Fields for an Supplemental document, which supplements a snapshot."""

    name: str
    timestamp: str
    creator: str
    snapshot_institution_values: dict[str, dict[str, Any]]
    admin_only: bool
    _id: ObjectId | None = None
    confirmation_touchstone_ts: int = 0  # zero for legacy data

    def snapshot_institution_values_as_dc(self) -> dict[str, uut.InstitutionValues]:
        """Get `snapshot_institution_values` as a dict of
        `InstitutionValues`s."""
        return {
            k: dacite.from_dict(uut.InstitutionValues, v)
            for k, v in self.snapshot_institution_values.items()
        }

    def override_all_institutions_touchstones(self) -> None:
        """Override all institutions touchstones with internal value."""
        for inst_vals in self.snapshot_institution_values.values():
            inst_vals["headcounts_metadata"][
                "confirmation_touchstone_ts"
            ] = self.confirmation_touchstone_ts

            inst_vals["table_metadata"][
                "confirmation_touchstone_ts"
            ] = self.confirmation_touchstone_ts

            inst_vals["computing_metadata"][
                "confirmation_touchstone_ts"
            ] = self.confirmation_touchstone_ts
