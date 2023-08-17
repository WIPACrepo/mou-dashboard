"""Custom type definitions."""

import dataclasses as dc
from typing import Any

import universal_utils.types as uut
from bson.objectid import ObjectId
from dacite import from_dict


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
            k: from_dict(uut.InstitutionValues, v)
            for k, v in self.snapshot_institution_values.items()
        }
