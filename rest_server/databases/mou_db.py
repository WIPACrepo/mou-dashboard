"""Database interface for MoU data."""

import asyncio
import base64
import io
import logging
import time
from typing import Any, Coroutine, Dict, List, Tuple, cast

import pandas as pd  # type: ignore[import]
import pymongo.errors  # type: ignore[import]
from motor.motor_tornado import MotorClient  # type: ignore
from tornado import web

from ..config import EXCLUDE_COLLECTIONS, EXCLUDE_DBS
from ..utils import types, utils
from ..utils.mongo_tools import Mongofier
from . import table_config_db as tc_db

_LIVE_COLLECTION = "LIVE_COLLECTION"


class DocumentNotFoundError(Exception):
    """Raised when a document is not found."""


class MoUDatabaseClient:
    """MotorClient with additional guardrails for MoU things."""

    def __init__(self, motor_client: MotorClient) -> None:
        tc_db_client = tc_db.TableConfigDatabaseClient(motor_client)
        self.data_adaptor = utils.MoUDataAdaptor(tc_db_client)

        self._mongo = motor_client

        def _run(f: Coroutine[Any, Any, Any]) -> Any:
            return asyncio.get_event_loop().run_until_complete(f)

        # check indexes
        _run(self._ensure_all_db_indexes())

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

    async def ingest_xlsx(  # pylint:disable=too-many-locals
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
        from ..utils.utils import TableConfigDataAdaptor  # pylint: disable=C0415

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
            if not all(
                k in self.data_adaptor.tc_db_client.get_columns() for k in row.keys()
            ):
                raise web.HTTPError(
                    422,
                    reason=f"Table not in correct format: "
                    f"XLSX's KEYS={row.keys()} vs "
                    f"ALLOWABLE KEYS={self.data_adaptor.tc_db_client.get_columns()})",
                )

        # mongofy table -- and verify data
        try:
            tc_adaptor = TableConfigDataAdaptor(self.data_adaptor.tc_db_client)
            table: types.Table = [
                self.data_adaptor.mongofy_record(
                    wbs_db,
                    tc_adaptor.remove_on_the_fly_fields(row),
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
            n for n in await self._mongo.list_database_names() if n not in EXCLUDE_DBS
        ]

    async def _list_collection_names(self, db: str) -> List[str]:
        """Return collection names in database."""
        return [
            n
            for n in await self._mongo[db].list_collection_names()
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
        doc = await self._mongo[f"{wbs_db}-supplemental"][snap_coll].find_one()
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

        coll_obj = self._mongo[f"{wbs_db}-supplemental"][snap_coll]
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
        await self._mongo[f"{wbs_db}-supplemental"].drop_collection(snap_coll)

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

        db_obj = self._mongo[wbs_db]

        # drop the collection if it already exists
        await db_obj.drop_collection(snap_coll)

        coll_obj = await db_obj.create_collection(snap_coll)
        await self._ensure_collection_indexes(wbs_db, snap_coll)

        # Ingest
        await coll_obj.insert_many(
            [self.data_adaptor.mongofy_record(wbs_db, r) for r in table]
        )

        # create supplemental document
        await self._create_supplemental_db_document(
            wbs_db, snap_coll, name, creator, all_insts_values, admin_only
        )

    async def _ensure_collection_indexes(self, wbs_db: str, snap_coll: str) -> None:
        """Create indexes in collection."""
        coll_obj = self._mongo[wbs_db][snap_coll]

        _inst = Mongofier.mongofy_key_name(tc_db.INSTITUTION)
        await coll_obj.create_index(_inst, name=f"{_inst}_index", unique=False)

        _labor = Mongofier.mongofy_key_name(tc_db.LABOR_CAT)
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
            query[Mongofier.mongofy_key_name(tc_db.LABOR_CAT)] = labor
        if institution:
            query[Mongofier.mongofy_key_name(tc_db.INSTITUTION)] = institution

        # build demongofied table
        table: types.Table = []
        i, dels = 0, 0
        async for record in self._mongo[wbs_db][snap_coll].find(query):
            if record.get(self.data_adaptor.IS_DELETED):
                dels += 1
                continue
            table.append(self.data_adaptor.demongofy_record(record))
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
        record = self.data_adaptor.mongofy_record(wbs_db, record)
        coll_obj = self._mongo[wbs_db][_LIVE_COLLECTION]

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

        return self.data_adaptor.demongofy_record(record)

    async def _set_is_deleted_status(
        self, wbs_db: str, record_id: str, is_deleted: bool, editor: str = ""
    ) -> types.Record:
        """Mark the record as deleted/not-deleted."""
        query = self.data_adaptor.mongofy_record(
            wbs_db,
            {tc_db.ID: record_id},
        )
        record: types.Record = await self._mongo[wbs_db][_LIVE_COLLECTION].find_one(
            query
        )

        record.update({self.data_adaptor.IS_DELETED: is_deleted})
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
