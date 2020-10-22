"""Database utilities."""

import asyncio
import base64
import io
import logging
import time
from typing import Any, cast, Coroutine, Dict, List, Optional, Tuple

import pandas as pd  # type: ignore[import]
from bson.objectid import ObjectId  # type: ignore[import]
from motor.motor_tornado import MotorClient  # type: ignore
from tornado import web

from .. import table_config as tc
from ..config import EXCLUDE_COLLECTIONS, EXCLUDE_DBS
from .types import InstitutionValues, Record, SnapshotInfo, SupplementalDoc, Table

IS_DELETED = "deleted"
_LIVE_COLLECTION = "LIVE_COLLECTION"


class DocumentNotFoundError(Exception):
    """Raised when a document is not found."""


class MoUMotorClient:
    """MotorClient with additional guardrails for MoU things."""

    def __init__(self, motor_client: MotorClient) -> None:
        self._client = motor_client

        def _run(f: Coroutine[Any, Any, Any]) -> Any:
            return asyncio.get_event_loop().run_until_complete(f)

        # check indexes
        _run(self._ensure_all_db_indexes())

    @staticmethod
    def _validate_record_data(record: Record) -> None:
        """Check that each value in a dropdown-type column is valid.

        If not, raise Exception.
        """
        for col_raw, value in record.items():
            col = MoUMotorClient._demongofy_key_name(col_raw)

            # Blanks are okay
            if not value:
                continue

            # Validate a simple dropdown column
            if col in tc.get_simple_dropdown_menus():
                if value in tc.get_simple_dropdown_menus()[col]:
                    continue
                raise Exception(f"Invalid Simple-Dropdown Data: {col=} {record=}")

            # Validate a conditional dropdown column
            if col in tc.get_conditional_dropdown_menus():
                parent_col, menus = tc.get_conditional_dropdown_menus()[col]

                # Get parent value
                if parent_col in record:
                    parent_value = record[parent_col]
                # Check mongofied version  # pylint: disable=C0325
                elif (mpc := MoUMotorClient._mongofy_key_name(parent_col)) in record:
                    parent_value = record[mpc]
                # Parent column is missing (*NOT* '' value)
                else:  # validate with any/all parents
                    if value in [v for _, vals in menus.items() for v in vals]:
                        continue
                    raise Exception(
                        f"{menus} Invalid Conditional-Dropdown (Orphan) Data: {col=} {record=}"
                    )

                # validate with parent value
                if parent_value and (value in menus[parent_value]):  # type: ignore[index]
                    continue
                raise Exception(f"Invalid Conditional-Dropdown Data: {col=} {record=}")

    @staticmethod
    def _mongofy_key_name(key: str) -> str:
        return key.replace(".", ";")

    @staticmethod
    def _demongofy_key_name(key: str) -> str:
        return key.replace(";", ".")

    @staticmethod
    def _mongofy_record(record: Record, assert_data: bool = True) -> Record:
        # assert data is valid
        if assert_data:
            MoUMotorClient._validate_record_data(record)
        # mongofy key names
        for key in list(record.keys()):
            record[MoUMotorClient._mongofy_key_name(key)] = record.pop(key)
        # cast ID
        if record.get(tc.ID):
            record[tc.ID] = ObjectId(record[tc.ID])

        return record

    @staticmethod
    def _demongofy_record(record: Record) -> Record:
        # replace Nones with ""
        for key in record.keys():
            if record[key] is None:
                record[key] = ""
        # demongofy key names
        for key in list(record.keys()):
            record[MoUMotorClient._demongofy_key_name(key)] = record.pop(key)
        record[tc.ID] = str(record[tc.ID])  # cast ID
        if IS_DELETED in record.keys():
            record.pop(IS_DELETED)

        return record

    async def _create_live_collection(
        self, snap_db: str, table: Table, creator: str
    ) -> None:
        """Create the live collection."""
        logging.debug(f"Creating Live Collection ({snap_db=})...")

        await self._ingest_new_collection(snap_db, _LIVE_COLLECTION, table, "", creator)

        logging.debug(f"Created Live Collection: ({snap_db=}) {len(table)} records.")

    async def ingest_xlsx(
        self, snap_db: str, base64_xlsx: str, filename: str, creator: str
    ) -> Tuple[str, str]:
        """Ingest the xlsx's data as the new Live Collection.

        Also make snapshots of the previous live table and the new one.
        """
        logging.info(f"Ingesting xlsx {filename} ({snap_db=})...")

        def _is_a_total_row(row: Record) -> bool:
            # check L2, L3, Inst., & US/Non-US  columns for "total" substring
            for key in [tc.WBS_L2, tc.WBS_L3, tc.INSTITUTION, tc.US_NON_US]:
                data = row.get(key)
                if isinstance(data, str) and ("TOTAL" in data.upper()):
                    return True
            return False

        def _row_has_data(row: Record) -> bool:
            # check purely blank rows
            if not any(row.values()):  # purely blank rows
                return False
            # check blanks except tc.WBS_L2, tc.WBS_L3, & tc.US_NON_US
            for key, val in row.items():
                if key in [tc.WBS_L2, tc.WBS_L3, tc.US_NON_US]:
                    continue
                if val:  # just need one value
                    return True
            return False

        # decode & read data from excel file
        # remove blanks and rows with "total" in them (case-insensitive)
        # format as if this was done via POST @ '/record'
        from . import utils  # pylint: disable=C0415

        try:
            decoded = base64.b64decode(base64_xlsx)
            df = pd.read_excel(io.BytesIO(decoded))
        except Exception as e:
            logging.error(str(e))
            raise web.HTTPError(400, reason=str(e))

        table: Table = [
            self._mongofy_record(utils.remove_on_the_fly_fields(row))
            for row in df.fillna("").to_dict("records")
            if _row_has_data(row) and not _is_a_total_row(row)
        ]
        logging.debug(f"xlsx table has {len(table)} records ({snap_db=}).")

        # snapshot, ingest, snapshot
        try:
            previous_snap = await self.snapshot_live_collection(
                snap_db, "State Before Table Replacement", f"{creator} (auto)"
            )
        except web.HTTPError as e:
            if e.status_code != 422:
                raise
            previous_snap = ""
        await self._create_live_collection(snap_db, table, creator)
        current_snap = await self.snapshot_live_collection(
            snap_db, f"Replacement Table ({filename})", creator
        )

        logging.debug(
            f"Ingested xlsx: {filename=}, {snap_db=}, {current_snap}, {previous_snap}."
        )
        return previous_snap, current_snap

    async def _list_database_names(self) -> List[str]:
        """Return all databases' names."""
        return [
            n for n in await self._client.list_database_names() if n not in EXCLUDE_DBS
        ]

    async def _list_collection_names(self, db: str) -> List[str]:
        """Return collection names in database."""
        return [
            n
            for n in await self._client[db].list_collection_names()
            if n not in EXCLUDE_COLLECTIONS
        ]

    async def get_snapshot_info(self, snap_db: str, snap_coll: str) -> SnapshotInfo:
        """Get the name of the snapshot."""
        logging.debug(f"Getting Snapshot Name ({snap_db=}, {snap_coll=})...")

        await self._check_database_state(snap_db)

        doc = await self._get_supplemental_doc(snap_db, snap_coll)

        logging.info(f"Snapshot Name [{doc['name']}] ({snap_db=}, {snap_coll=})...")
        return {
            "name": doc["name"],
            "creator": doc["creator"],
            "timestamp": doc["timestamp"],
        }

    async def upsert_institution_values(
        self, snap_db: str, institution: str, vals: InstitutionValues
    ) -> None:
        """Upsert the values for an institution."""
        logging.debug(
            f"Upserting Institution's Values ({snap_db=}, {institution=}, {vals=})..."
        )

        await self._check_database_state(snap_db)

        doc = await self._get_supplemental_doc(snap_db, _LIVE_COLLECTION)
        doc["snapshot_institution_values"].update({institution: vals})
        await self._set_supplemental_doc(snap_db, _LIVE_COLLECTION, doc)

        logging.info(
            f"Upserted Institution's Values ({snap_db=}, {institution=}, {vals=})."
        )

    async def _check_database_state(self, snap_db: str) -> None:
        """Raise 422 if there are no collections."""
        if await self._list_collection_names(snap_db):
            return

        logging.error(f"Snapshot Database has no collections ({snap_db=}).")
        raise web.HTTPError(
            422, reason=f"Snapshot Database has no collections ({snap_db=}).",
        )

    async def get_institution_values(
        self, snap_db: str, snapshot_timestamp: str, institution: str,
    ) -> InstitutionValues:
        """Get the values for an institution."""
        logging.debug(f"Getting Institution's Values ({snap_db=}, {institution=})...")

        await self._check_database_state(snap_db)

        vals: InstitutionValues = {
            "phds_authors": 0,
            "faculty": 0,
            "scientists_post_docs": 0,
            "grad_students": 0,
            "text": "",
        }

        if not snapshot_timestamp:
            snapshot_timestamp = _LIVE_COLLECTION

        doc = await self._get_supplemental_doc(snap_db, snapshot_timestamp)

        try:
            vals = doc["snapshot_institution_values"][institution]
            logging.info(f"Institution's Values [{vals}] ({snap_db=}, {institution=}).")
            return vals
        except KeyError:
            logging.info(f"Institution has no values ({snap_db=}, {institution=}).")
            return vals

    async def _get_supplemental_doc(
        self, snap_db: str, snap_coll: str
    ) -> SupplementalDoc:
        doc = await self._client[f"{snap_db}-supplemental"][snap_coll].find_one()
        if not doc:
            raise DocumentNotFoundError(
                f"No Supplemental document found for {snap_coll=}."
            )

        if doc["timestamp"] != snap_coll:
            raise web.HTTPError(
                500,
                reason=f"Erroneous supplemental document found: {snap_coll=}, {doc=}",
            )

        return cast(SupplementalDoc, doc)

    async def _set_supplemental_doc(
        self, snap_db: str, snap_coll: str, doc: SupplementalDoc
    ) -> None:
        """Insert/update a Supplemental document."""
        if snap_coll != doc["timestamp"]:
            raise web.HTTPError(
                400,
                reason=f"Tried to set erroneous supplemental document: {snap_coll=}, {doc=}",
            )

        coll_obj = self._client[f"{snap_db}-supplemental"][snap_coll]
        await coll_obj.replace_one({"timestamp": doc["timestamp"]}, doc, upsert=True)

    async def _create_supplemental_db_document(
        self,
        snap_db: str,
        snap_coll: str,
        name: str,
        creator: str,
        all_insts_values: Optional[Dict[str, InstitutionValues]] = None,
    ) -> None:
        logging.debug(
            f"Creating Supplemental DB/Document ({snap_db=}, {snap_coll=})..."
        )

        # drop the collection if it already exists
        await self._client[f"{snap_db}-supplemental"].drop_collection(snap_coll)

        # populate the singleton document
        doc: SupplementalDoc = {
            "name": name,
            "timestamp": snap_coll,
            "creator": creator,
            "snapshot_institution_values": all_insts_values if all_insts_values else {},
        }
        await self._set_supplemental_doc(snap_db, snap_coll, doc)

        logging.debug(
            f"Created Supplemental Document ({snap_db=}, {snap_coll=}): {await self._get_supplemental_doc(snap_db, snap_coll)}."
        )

    async def _ingest_new_collection(  # pylint: disable=R0913
        self,
        snap_db: str,
        snap_coll: str,
        table: Table,
        name: str,
        creator: str,
        all_insts_values: Optional[Dict[str, InstitutionValues]] = None,
    ) -> None:
        """Add table to a new collection.

        If collection already exists, replace.
        """
        db_obj = self._client[snap_db]

        # drop the collection if it already exists
        await db_obj.drop_collection(snap_coll)

        coll_obj = await db_obj.create_collection(snap_coll)
        await self._ensure_collection_indexes(snap_db, snap_coll)

        # Ingest
        await coll_obj.insert_many([self._mongofy_record(r) for r in table])

        # create supplemental document
        await self._create_supplemental_db_document(
            snap_db, snap_coll, name, creator, all_insts_values
        )

    async def _ensure_collection_indexes(self, snap_db: str, snap_coll: str) -> None:
        """Create indexes in collection."""
        coll_obj = self._client[snap_db][snap_coll]

        _inst = self._mongofy_key_name(tc.INSTITUTION)
        await coll_obj.create_index(_inst, name=f"{_inst}_index", unique=False)

        _labor = self._mongofy_key_name(tc.LABOR_CAT)
        await coll_obj.create_index(_labor, name=f"{_labor}_index", unique=False)

        async for index in coll_obj.list_indexes():
            logging.debug(index)

    async def _ensure_all_db_indexes(self) -> None:
        """Create all indexes in all databases."""
        logging.debug("Ensuring All Databases' Indexes...")

        for snap_db in await self._list_database_names():
            for snap_coll in await self._list_collection_names(snap_db):
                await self._ensure_collection_indexes(snap_db, snap_coll)

        logging.debug("Ensured All Databases' Indexes.")

    async def get_table(
        self, snap_db: str, snap_coll: str = "", labor: str = "", institution: str = ""
    ) -> Table:
        """Return the table from the collection name."""
        if not snap_coll:
            snap_coll = _LIVE_COLLECTION

        logging.debug(f"Getting from {snap_coll} ({snap_db=})...")

        await self._check_database_state(snap_db)

        query = {}
        if labor:
            query[self._mongofy_key_name(tc.LABOR_CAT)] = labor
        if institution:
            query[self._mongofy_key_name(tc.INSTITUTION)] = institution

        # build demongofied table
        table: Table = []
        i, dels = 0, 0
        async for record in self._client[snap_db][snap_coll].find(query):
            if record.get(IS_DELETED):
                dels += 1
                continue
            table.append(self._demongofy_record(record))
            i += 1

        logging.info(
            f"Table [{snap_db=} {snap_coll=}] ({institution=}, {labor=}) has {i} records (and {dels} deleted records)."
        )

        return table

    async def upsert_record(self, snap_db: str, record: Record) -> Record:
        """Insert a record.

        Update if it already exists.
        """
        logging.debug(f"Upserting {record} ({snap_db=})...")

        await self._check_database_state(snap_db)

        record = self._mongofy_record(record)
        coll_obj = self._client[snap_db][_LIVE_COLLECTION]

        # if record has an ID -- replace it
        if record.get(tc.ID):
            res = await coll_obj.replace_one({tc.ID: record[tc.ID]}, record)
            logging.info(f"Updated {record} ({snap_db=}).")
        # otherwise -- create it
        else:
            record.pop(tc.ID)
            res = await coll_obj.insert_one(record)
            record[tc.ID] = res.inserted_id
            logging.info(f"Inserted {record} ({snap_db=}).")

        return self._demongofy_record(record)

    async def _set_is_deleted_status(
        self, snap_db: str, record_id: str, is_deleted: bool
    ) -> Record:
        """Mark the record as deleted/not-deleted."""
        query = self._mongofy_record({tc.ID: record_id})
        record: Record = await self._client[snap_db][_LIVE_COLLECTION].find_one(query)

        record.update({IS_DELETED: is_deleted})
        record = await self.upsert_record(snap_db, record)

        return record

    async def delete_record(self, snap_db: str, record_id: str) -> Record:
        """Mark the record as deleted."""
        logging.debug(f"Deleting {record_id} ({snap_db=})...")

        await self._check_database_state(snap_db)

        record = await self._set_is_deleted_status(snap_db, record_id, True)

        logging.info(f"Deleted {record} ({snap_db=}).")
        return record

    async def snapshot_live_collection(
        self, snap_db: str, name: str, creator: str
    ) -> str:
        """Create a snapshot collection by copying the live collection."""
        logging.debug(f"Snapshotting ({snap_db=}, {creator=})...")

        await self._check_database_state(snap_db)

        table = await self.get_table(snap_db, _LIVE_COLLECTION)
        supplemental_doc = await self._get_supplemental_doc(snap_db, _LIVE_COLLECTION)

        snap_coll = str(time.time())
        await self._ingest_new_collection(
            snap_db,
            snap_coll,
            table,
            name,
            creator,
            supplemental_doc["snapshot_institution_values"],
        )

        logging.info(f"Snapshotted {snap_coll} ({snap_db=}, {creator=}).")
        return snap_coll

    async def list_snapshot_timestamps(self, snap_db: str) -> List[str]:
        """Return a list of the snapshot collections."""
        logging.info(f"Getting Snapshot Timestamps ({snap_db=})...")

        await self._check_database_state(snap_db)

        snapshots = [
            c
            for c in await self._list_collection_names(snap_db)
            if c != _LIVE_COLLECTION
        ]

        logging.debug(f"Snapshot Timestamps {snapshots} ({snap_db=}).")
        return snapshots

    async def restore_record(self, snap_db: str, record_id: str) -> None:
        """Mark the record as not deleted."""
        logging.debug(f"Restoring {record_id} ({snap_db=})...")

        await self._check_database_state(snap_db)

        record = await self._set_is_deleted_status(snap_db, record_id, False)

        logging.info(f"Restored {record} ({snap_db=}).")
