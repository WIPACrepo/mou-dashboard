"""Database interface for MoU data."""

import asyncio
import base64
import io
import logging
import time
from typing import Any, Coroutine, Dict, List, Tuple, cast

import pandas as pd  # type: ignore[import]
import pymongo.errors  # type: ignore[import]
from bson.objectid import ObjectId  # type: ignore[import]
from motor.motor_tornado import MotorClient  # type: ignore
from tornado import web

from ..config import EXCLUDE_COLLECTIONS, EXCLUDE_DBS
from ..utils import types
from . import table_config_db as tc_db

IS_DELETED = "deleted"
_LIVE_COLLECTION = "LIVE_COLLECTION"


class DocumentNotFoundError(Exception):
    """Raised when a document is not found."""


class MoUDatabaseClient:
    """MotorClient with additional guardrails for MoU things."""

    def __init__(self, motor_client: MotorClient) -> None:
        self.tc_db_client = tc_db.TableConfigDatabaseClient(motor_client)
        self._client = motor_client

        def _run(f: Coroutine[Any, Any, Any]) -> Any:
            return asyncio.get_event_loop().run_until_complete(f)

        # check indexes
        _run(self._ensure_all_db_indexes())

    @staticmethod
    def _validate_record_data(
        wbs_db: str, record: types.Record, tc_db_client: tc_db.TableConfigDatabaseClient
    ) -> None:
        """Check that each value in a dropdown-type column is valid.

        If not, raise Exception.
        """
        for col_raw, value in record.items():
            col = MoUDatabaseClient._demongofy_key_name(col_raw)

            # Blanks are okay
            if not value:
                continue

            # Validate a simple dropdown column
            if col in tc_db_client.get_simple_dropdown_menus(wbs_db):
                if value in tc_db_client.get_simple_dropdown_menus(wbs_db)[col]:
                    continue
                raise Exception(f"Invalid Simple-Dropdown Data: {col=} {record=}")

            # Validate a conditional dropdown column
            if col in tc_db_client.get_conditional_dropdown_menus(wbs_db):
                parent_col, menus = tc_db_client.get_conditional_dropdown_menus(wbs_db)[
                    col
                ]

                # Get parent value
                if parent_col in record:
                    parent_value = record[parent_col]
                # Check mongofied version  # pylint: disable=C0325
                elif (mpc := MoUDatabaseClient._mongofy_key_name(parent_col)) in record:
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
    def _mongofy_record(
        wbs_db: str,
        record: types.Record,
        tc_db_client: tc_db.TableConfigDatabaseClient,
        assert_data: bool = True,
    ) -> types.Record:
        # assert data is valid
        if assert_data:
            MoUDatabaseClient._validate_record_data(wbs_db, record, tc_db_client)
        # mongofy key names
        for key in list(record.keys()):
            record[MoUDatabaseClient._mongofy_key_name(key)] = record.pop(key)
        # cast ID
        if record.get(tc_db.ID):
            record[tc_db.ID] = ObjectId(record[tc_db.ID])

        return record

    @staticmethod
    def _demongofy_record(record: types.Record) -> types.Record:
        # replace Nones with ""
        for key in record.keys():
            if record[key] is None:
                record[key] = ""
        # demongofy key names
        for key in list(record.keys()):
            record[MoUDatabaseClient._demongofy_key_name(key)] = record.pop(key)
        record[tc_db.ID] = str(record[tc_db.ID])  # cast ID
        if IS_DELETED in record.keys():
            record.pop(IS_DELETED)

        return record

    async def _create_live_collection(  # pylint: disable=R0913
        self,
        wbs_db: str,
        table: types.Table,
        creator: str,
        all_insts_values: Dict[str, types.InstitutionValues],
    ) -> None:
        """Create the live collection."""
        logging.debug(f"Creating Live Collection ({wbs_db=})...")

        for record in table:
            record.update({tc_db.EDITOR: "", tc_db.TIMESTAMP: time.time()})

        await self._ingest_new_collection(
            wbs_db, _LIVE_COLLECTION, table, "", creator, all_insts_values, False
        )

        logging.debug(f"Created Live Collection: ({wbs_db=}) {len(table)} records.")

    async def ingest_xlsx(
        self, wbs_db: str, base64_xlsx: str, filename: str, creator: str
    ) -> Tuple[str, str]:
        """Ingest the xlsx's data as the new Live Collection.

        Also make snapshots of the previous live table and the new one.
        """
        logging.info(f"Ingesting xlsx {filename} ({wbs_db=})...")

        def _is_a_total_row(row: types.Record) -> bool:
            # check L2, L3, Inst., & US/Non-US  columns for "total" substring
            for key in [tc_db.WBS_L2, tc_db.WBS_L3, tc_db.INSTITUTION, tc_db.US_NON_US]:
                data = row.get(key)
                if isinstance(data, str) and ("TOTAL" in data.upper()):
                    return True
            return False

        def _row_has_data(row: types.Record) -> bool:
            # check purely blank rows
            if not any(row.values()):  # purely blank rows
                return False
            # check blanks except tc.WBS_L2, tc.WBS_L3, & tc.US_NON_US
            for key, val in row.items():
                if key in [tc_db.WBS_L2, tc_db.WBS_L3, tc_db.US_NON_US]:
                    continue
                if val:  # just need one value
                    return True
            return False

        # decode & read data from excel file
        # remove blanks and rows with "total" in them (case-insensitive)
        # format as if this was done via POST @ '/record'
        from ..utils import utils  # pylint: disable=C0415

        # decode base64-excel
        try:
            decoded = base64.b64decode(base64_xlsx)
            df = pd.read_excel(io.BytesIO(decoded))  # pylint:disable=invalid-name
            raw_table = df.fillna("").to_dict("records")
        except Exception as e:
            raise web.HTTPError(400, reason=str(e))

        # check schema -- aka verify column names
        for row in raw_table:
            # check for extra keys
            if not all(k in self.tc_db_client.get_columns() for k in row.keys()):
                raise web.HTTPError(
                    422,
                    reason=f"Table not in correct format: "
                    f"XLSX's KEYS={row.keys()} vs "
                    f"ALLOWABLE KEYS={self.tc_db_client.get_columns()})",
                )

        # mongofy table -- and verify data
        try:
            table: types.Table = [
                self._mongofy_record(
                    wbs_db, utils.remove_on_the_fly_fields(row), self.tc_db_client
                )
                for row in raw_table
                if _row_has_data(row) and not _is_a_total_row(row)
            ]
        except Exception as e:
            raise web.HTTPError(422, reason=str(e))
        logging.debug(f"xlsx table has {len(table)} records ({wbs_db=}).")

        # snapshot
        try:
            previous_snap = await self.snapshot_live_collection(
                wbs_db, "Before Import", f"{creator} (auto)", admin_only=True
            )
        except web.HTTPError as e:
            if e.status_code != 422:
                raise
            previous_snap = ""

        # ingest
        try:
            doc = await self._get_supplemental_doc(wbs_db, previous_snap)
            all_insts_values = doc["snapshot_institution_values"]
        except (DocumentNotFoundError, pymongo.errors.InvalidName):
            all_insts_values = dict()
        await self._create_live_collection(wbs_db, table, creator, all_insts_values)

        # snapshot
        current_snap = await self.snapshot_live_collection(
            wbs_db, "Initial Import", creator, admin_only=True
        )

        logging.debug(
            f"Ingested xlsx: {filename=}, {wbs_db=}, {current_snap}, {previous_snap}."
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

    async def get_snapshot_info(
        self, wbs_db: str, snap_coll: str
    ) -> types.SnapshotInfo:
        """Get the name of the snapshot."""
        logging.debug(f"Getting Snapshot Name ({wbs_db=}, {snap_coll=})...")

        await self._check_database_state(wbs_db)

        doc = await self._get_supplemental_doc(wbs_db, snap_coll)

        logging.info(f"Snapshot Name [{doc['name']}] ({wbs_db=}, {snap_coll=})...")
        return {
            "name": doc["name"],
            "creator": doc["creator"],
            "timestamp": doc["timestamp"],
            "admin_only": doc["admin_only"],
        }

    async def upsert_institution_values(
        self, wbs_db: str, institution: str, vals: types.InstitutionValues
    ) -> None:
        """Upsert the values for an institution."""
        logging.debug(
            f"Upserting Institution's Values ({wbs_db=}, {institution=}, {vals=})..."
        )

        await self._check_database_state(wbs_db)

        doc = await self._get_supplemental_doc(wbs_db, _LIVE_COLLECTION)
        doc["snapshot_institution_values"].update({institution: vals})
        await self._set_supplemental_doc(wbs_db, _LIVE_COLLECTION, doc)

        logging.info(
            f"Upserted Institution's Values ({wbs_db=}, {institution=}, {vals=})."
        )

    async def _check_database_state(self, wbs_db: str) -> None:
        """Raise 422 if there are no collections."""
        if await self._list_collection_names(wbs_db):
            return

        logging.error(f"Snapshot Database has no collections ({wbs_db=}).")
        raise web.HTTPError(
            422,
            reason=f"Snapshot Database has no collections ({wbs_db=}).",
        )

    async def get_institution_values(
        self,
        wbs_db: str,
        snapshot_timestamp: str,
        institution: str,
    ) -> types.InstitutionValues:
        """Get the values for an institution."""
        logging.debug(f"Getting Institution's Values ({wbs_db=}, {institution=})...")

        await self._check_database_state(wbs_db)

        vals: types.InstitutionValues = {
            "phds_authors": None,
            "faculty": None,
            "scientists_post_docs": None,
            "grad_students": None,
            "cpus": None,
            "gpus": None,
            "text": "",
            "headcounts_confirmed": False,
            "computing_confirmed": False,
        }

        if not snapshot_timestamp:
            snapshot_timestamp = _LIVE_COLLECTION

        try:
            doc = await self._get_supplemental_doc(wbs_db, snapshot_timestamp)
        except DocumentNotFoundError as e:
            logging.warning(str(e))
            return vals

        try:
            vals = doc["snapshot_institution_values"][institution]
            logging.info(f"Institution's Values [{vals}] ({wbs_db=}, {institution=}).")
            return vals
        except KeyError:
            logging.info(f"Institution has no values ({wbs_db=}, {institution=}).")
            return vals

    async def _get_supplemental_doc(
        self, wbs_db: str, snap_coll: str
    ) -> types.SupplementalDoc:
        doc = await self._client[f"{wbs_db}-supplemental"][snap_coll].find_one()
        if not doc:
            raise DocumentNotFoundError(
                f"No Supplemental document found for {snap_coll=}."
            )

        if doc["timestamp"] != snap_coll:
            raise web.HTTPError(
                500,
                reason=f"Erroneous supplemental document found: {snap_coll=}, {doc=}",
            )

        return cast(types.SupplementalDoc, doc)

    async def _set_supplemental_doc(
        self, wbs_db: str, snap_coll: str, doc: types.SupplementalDoc
    ) -> None:
        """Insert/update a Supplemental document."""
        if snap_coll != doc["timestamp"]:
            raise web.HTTPError(
                400,
                reason=f"Tried to set erroneous supplemental document: {snap_coll=}, {doc=}",
            )

        coll_obj = self._client[f"{wbs_db}-supplemental"][snap_coll]
        await coll_obj.replace_one({"timestamp": doc["timestamp"]}, doc, upsert=True)

    async def _create_supplemental_db_document(  # pylint: disable=R0913
        self,
        wbs_db: str,
        snap_coll: str,
        name: str,
        creator: str,
        all_insts_values: Dict[str, types.InstitutionValues],
        admin_only: bool,
    ) -> None:
        logging.debug(f"Creating Supplemental DB/Document ({wbs_db=}, {snap_coll=})...")

        # drop the collection if it already exists
        await self._client[f"{wbs_db}-supplemental"].drop_collection(snap_coll)

        # populate the singleton document
        doc: types.SupplementalDoc = {
            "name": name,
            "timestamp": snap_coll,
            "creator": creator,
            "snapshot_institution_values": all_insts_values if all_insts_values else {},
            "admin_only": admin_only,
        }
        await self._set_supplemental_doc(wbs_db, snap_coll, doc)

        logging.debug(
            f"Created Supplemental Document ({wbs_db=}, {snap_coll=}): "
            f"{await self._get_supplemental_doc(wbs_db, snap_coll)}."
        )

    async def _ingest_new_collection(  # pylint: disable=R0913
        self,
        wbs_db: str,
        snap_coll: str,
        table: types.Table,
        name: str,
        creator: str,
        all_insts_values: Dict[str, types.InstitutionValues],
        admin_only: bool,
    ) -> None:
        """Add table to a new collection.

        If collection already exists, replace.
        """
        if admin_only and snap_coll == _LIVE_COLLECTION:
            raise Exception(
                f"A Live Collection cannot be admin-only ({wbs_db=} {snap_coll=} {admin_only=})."
            )

        if admin_only:
            name = f"{name} (admin-only)"

        db_obj = self._client[wbs_db]

        # drop the collection if it already exists
        await db_obj.drop_collection(snap_coll)

        coll_obj = await db_obj.create_collection(snap_coll)
        await self._ensure_collection_indexes(wbs_db, snap_coll)

        # Ingest
        await coll_obj.insert_many(
            [self._mongofy_record(wbs_db, r, self.tc_db_client) for r in table]
        )

        # create supplemental document
        await self._create_supplemental_db_document(
            wbs_db, snap_coll, name, creator, all_insts_values, admin_only
        )

    async def _ensure_collection_indexes(self, wbs_db: str, snap_coll: str) -> None:
        """Create indexes in collection."""
        coll_obj = self._client[wbs_db][snap_coll]

        _inst = self._mongofy_key_name(tc_db.INSTITUTION)
        await coll_obj.create_index(_inst, name=f"{_inst}_index", unique=False)

        _labor = self._mongofy_key_name(tc_db.LABOR_CAT)
        await coll_obj.create_index(_labor, name=f"{_labor}_index", unique=False)

        async for index in coll_obj.list_indexes():
            logging.debug(index)

    async def _ensure_all_db_indexes(self) -> None:
        """Create all indexes in all databases."""
        logging.debug("Ensuring All Databases' Indexes...")

        for wbs_db in await self._list_database_names():
            for snap_coll in await self._list_collection_names(wbs_db):
                await self._ensure_collection_indexes(wbs_db, snap_coll)

        logging.debug("Ensured All Databases' Indexes.")

    async def get_table(
        self, wbs_db: str, snap_coll: str = "", labor: str = "", institution: str = ""
    ) -> types.Table:
        """Return the table from the collection name."""
        if not snap_coll:
            snap_coll = _LIVE_COLLECTION

        logging.debug(f"Getting from {snap_coll} ({wbs_db=})...")

        await self._check_database_state(wbs_db)

        query = {}
        if labor:
            query[self._mongofy_key_name(tc_db.LABOR_CAT)] = labor
        if institution:
            query[self._mongofy_key_name(tc_db.INSTITUTION)] = institution

        # build demongofied table
        table: types.Table = []
        i, dels = 0, 0
        async for record in self._client[wbs_db][snap_coll].find(query):
            if record.get(IS_DELETED):
                dels += 1
                continue
            table.append(self._demongofy_record(record))
            i += 1

        logging.info(
            f"Table [{wbs_db=} {snap_coll=}] ({institution=}, {labor=}) "
            f"has {i} records (and {dels} deleted records)."
        )

        return table

    async def upsert_record(
        self, wbs_db: str, record: types.Record, editor: str
    ) -> types.Record:
        """Insert a record.

        Update if it already exists.
        """
        logging.debug(f"Upserting {record} ({wbs_db=})...")

        await self._check_database_state(wbs_db)

        # record timestamp and editor's name
        record[tc_db.TIMESTAMP] = time.time()
        if editor:
            record[tc_db.EDITOR] = editor

        # prep
        record = self._mongofy_record(wbs_db, record, self.tc_db_client)
        coll_obj = self._client[wbs_db][_LIVE_COLLECTION]

        # if record has an ID -- replace it
        if record.get(tc_db.ID):
            res = await coll_obj.replace_one({tc_db.ID: record[tc_db.ID]}, record)
            logging.info(f"Updated {record} ({wbs_db=}).")
        # otherwise -- create it
        else:
            record.pop(tc_db.ID)
            res = await coll_obj.insert_one(record)
            record[tc_db.ID] = res.inserted_id
            logging.info(f"Inserted {record} ({wbs_db=}).")

        return self._demongofy_record(record)

    async def _set_is_deleted_status(
        self, wbs_db: str, record_id: str, is_deleted: bool, editor: str = ""
    ) -> types.Record:
        """Mark the record as deleted/not-deleted."""
        query = self._mongofy_record(wbs_db, {tc_db.ID: record_id}, self.tc_db_client)
        record: types.Record = await self._client[wbs_db][_LIVE_COLLECTION].find_one(
            query
        )

        record.update({IS_DELETED: is_deleted})
        record = await self.upsert_record(wbs_db, record, editor)

        return record

    async def delete_record(
        self, wbs_db: str, record_id: str, editor: str
    ) -> types.Record:
        """Mark the record as deleted."""
        logging.debug(f"Deleting {record_id} ({wbs_db=})...")

        await self._check_database_state(wbs_db)

        record = await self._set_is_deleted_status(wbs_db, record_id, True, editor)

        logging.info(f"Deleted {record} ({wbs_db=}).")
        return record

    async def snapshot_live_collection(
        self, wbs_db: str, name: str, creator: str, admin_only: bool
    ) -> str:
        """Create a snapshot collection by copying the live collection."""
        logging.debug(f"Snapshotting ({wbs_db=}, {creator=})...")

        await self._check_database_state(wbs_db)

        table = await self.get_table(wbs_db, _LIVE_COLLECTION)
        supplemental_doc = await self._get_supplemental_doc(wbs_db, _LIVE_COLLECTION)

        snap_coll = str(time.time())
        await self._ingest_new_collection(
            wbs_db,
            snap_coll,
            table,
            name,
            creator,
            supplemental_doc["snapshot_institution_values"],
            admin_only,
        )

        # set all *_confirmed values to False
        for inst, vals in supplemental_doc["snapshot_institution_values"].items():
            vals["headcounts_confirmed"] = False
            vals["computing_confirmed"] = False
            await self.upsert_institution_values(wbs_db, inst, vals)

        logging.info(f"Snapshotted {snap_coll} ({wbs_db=}, {creator=}).")
        return snap_coll

    async def _is_snapshot_admin_only(self, wbs_db: str, name: str) -> bool:
        doc = await self._get_supplemental_doc(wbs_db, name)
        return doc["admin_only"]

    async def list_snapshot_timestamps(
        self, wbs_db: str, exclude_admin_snaps: bool
    ) -> List[str]:
        """Return a list of the snapshot collections."""
        logging.info(f"Getting Snapshot Timestamps ({wbs_db=})...")

        await self._check_database_state(wbs_db)

        snapshots = [
            c
            for c in await self._list_collection_names(wbs_db)
            if c != _LIVE_COLLECTION
        ]

        if exclude_admin_snaps:
            snapshots = [
                s
                for s in snapshots
                if not await self._is_snapshot_admin_only(wbs_db, s)
            ]

        logging.debug(f"Snapshot Timestamps {snapshots} ({wbs_db=}).")
        return snapshots

    async def restore_record(self, wbs_db: str, record_id: str) -> None:
        """Mark the record as not deleted."""
        logging.debug(f"Restoring {record_id} ({wbs_db=})...")

        await self._check_database_state(wbs_db)

        record = await self._set_is_deleted_status(wbs_db, record_id, False)

        logging.info(f"Restored {record} ({wbs_db=}).")
