"""Custom type definitions."""

import dataclasses as dc
from typing import Dict

import universal_utils.types as uut
from bson.objectid import ObjectId


@dc.dataclass(frozen=True)
class SupplementalDoc:
    """Fields for an Supplemental document, which supplements a snapshot."""

    name: str
    timestamp: str
    creator: str
    snapshot_institution_values: Dict[str, uut.InstitutionValues]
    admin_only: bool
    _id: ObjectId | None = None
