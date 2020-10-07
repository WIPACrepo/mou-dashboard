"""Database utilities."""

import asyncio
import base64
import io
import logging
import time
from typing import Any, Coroutine, List

import pandas as pd  # type: ignore[import]
from bson.objectid import ObjectId  # type: ignore[import]
from motor.motor_tornado import (  # type: ignore
    MotorClient,
    MotorCollection,
    MotorDatabase,
)
from tornado import web

from .. import table_config as tc
from ..config import EXCLUDE_COLLECTIONS, EXCLUDE_DBS, SNAPSHOTS_DB
from .types import Record, Table

IS_DELETED = "deleted"
_LIVE_COLLECTION = "LIVE_COLLECTION"


class MoUMotorClient:
    """MotorClient with additional guardrails for MoU things."""

    def __init__(self, motor_client: MotorClient) -> None:
        self._client = motor_client

        def _run(f: Coroutine[Any, Any, Any]) -> Any:
            return asyncio.get_event_loop().run_until_complete(f)

        # check indexes
        _run(self._ensure_all_databases_indexes())

    @staticmethod
    def _validate_record_data(record: Record) -> None:
        """Check that each value in a dropdown-type column is valid.

        If not, raise Exception.
        """
        categories = {}
        for col, opts in tc.get_simple_dropdown_menus().items():
            categories[col] = opts
        for col, conditions in tc.get_conditional_dropdown_menus().items():
            categories[col] = [opt for menu in conditions[1].values() for opt in menu]

        logging.debug(record)
        for cat, options in categories.items():
            try:
                # assume record is demongofied
                if record[cat] in options:
                    continue
            except KeyError:
                if record[MoUMotorClient._mongofy_key_name(cat)] in options:
                    continue
            raise Exception(f"Invalid Data: column={cat} {record}")

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

    async def _create_live_collection(self, table: Table) -> None:
        """Create the live collection."""
        logging.debug("Creating Live Collection...")
        await self._ingest_new_collection(_LIVE_COLLECTION, table)
        logging.debug(f"Created Live Collection: {len(table)} records.")

    async def ingest_xlsx(self, base64_xlsx: str, filename: str) -> str:
        """Ingest the xlsx's data as the new Live Collection.

        Also make snapshot.
        """
        logging.info(f"Ingesting xlsx {filename}...")

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
        logging.debug(f"xlsx table has {len(table)} records.")

        # ingest
        await self._create_live_collection(table)
        collection = await self.snapshot_live_collection()

        logging.debug(f"Ingested xlsx {filename}; Collection {collection}.")
        return collection

    async def _list_database_names(self) -> List[str]:
        """Return all databases' names."""
        return [
            n for n in await self._client.list_database_names() if n not in EXCLUDE_DBS
        ]

    def _get_db(self, db: str = SNAPSHOTS_DB) -> MotorDatabase:
        """Return database instance."""
        try:
            return self._client[db]
        except (KeyError, TypeError):
            raise web.HTTPError(400, reason=f"database not found ({db})")

    async def _list_collection_names(self, db: str = SNAPSHOTS_DB) -> List[str]:
        """Return collection names in database."""
        return [
            n
            for n in await self._get_db(db).list_collection_names()
            if n not in EXCLUDE_COLLECTIONS
        ]

    def _get_collection(
        self, collection: str, db: str = SNAPSHOTS_DB
    ) -> MotorCollection:
        """Return collection instance."""
        try:
            return self._get_db(db)[collection]
        except KeyError:
            raise web.HTTPError(400, reason=f"collection not found ({collection})")

    async def _ingest_new_collection(
        self, collection: str, table: Table, db: str = SNAPSHOTS_DB
    ) -> None:
        """Add table to a new collection.

        If collection already exists, replace.
        """
        # Create
        db_obj = self._get_db(db)
        try:
            # drop the collection if it already exists.
            coll_obj = db_obj[collection]
            await coll_obj.drop()
        except KeyError:
            pass

        coll_obj = await db_obj.create_collection(collection)
        await self._ensure_collection_indexes(collection, db)

        # Ingest
        await coll_obj.insert_many([self._mongofy_record(r) for r in table])

    async def _ensure_collection_indexes(
        self, collection: str, db: str = SNAPSHOTS_DB
    ) -> None:
        """Create indexes in collection."""
        coll_obj = self._get_collection(collection, db)

        _inst = self._mongofy_key_name(tc.INSTITUTION)
        await coll_obj.create_index(_inst, name=f"{_inst}_index", unique=False)

        _labor = self._mongofy_key_name(tc.LABOR_CAT)
        await coll_obj.create_index(_labor, name=f"{_labor}_index", unique=False)

        async for index in coll_obj.list_indexes():
            logging.debug(index)

    async def _ensure_all_databases_indexes(self) -> None:
        """Create all indexes in all databases."""
        logging.debug("Ensuring All Databases' Indexes...")

        for db in await self._list_database_names():
            for collection in await self._list_collection_names(db):
                await self._ensure_collection_indexes(collection, db)

        logging.debug("Ensured All Databases' Indexes.")

    async def get_table(
        self, collection: str = "", labor: str = "", institution: str = ""
    ) -> Table:
        """Return the table from the collection name."""
        if not collection:
            collection = _LIVE_COLLECTION

        logging.debug(f"Getting from {collection}...")

        query = {}
        if labor:
            query[self._mongofy_key_name(tc.LABOR_CAT)] = labor
        if institution:
            query[self._mongofy_key_name(tc.INSTITUTION)] = institution

        # build demongofied table
        table: Table = []
        i, dels = 0, 0
        async for record in self._get_collection(collection).find(query):
            if record.get(IS_DELETED):
                dels += 1
                continue
            table.append(self._demongofy_record(record))
            i += 1

        logging.info(
            f"Table [{collection=}] ({institution=}, {labor=}) has {i} records (and {dels} deleted records)."
        )

        return table

    async def upsert_record(self, record: Record) -> Record:
        """Insert a record.

        Update if it already exists.
        """
        logging.debug(f"Upserting {record}...")

        record = self._mongofy_record(record)
        collection_obj = self._get_collection(_LIVE_COLLECTION)

        # if record has an ID -- replace it
        if record.get(tc.ID):
            res = await collection_obj.replace_one({tc.ID: record[tc.ID]}, record)
            logging.info(f"Updated {record}.")
        # otherwise -- create it
        else:
            record.pop(tc.ID)
            res = await collection_obj.insert_one(record)
            record[tc.ID] = res.inserted_id
            logging.info(f"Inserted {record}.")

        return self._demongofy_record(record)

    async def delete_record(self, record: Record) -> Record:
        """Mark the record as deleted."""
        logging.debug(f"Deleting {record}...")

        record.update({IS_DELETED: True})
        record = await self.upsert_record(record)

        logging.info(f"Deleted {record}.")
        return record

    async def snapshot_live_collection(self) -> str:
        """Create a collection by copying the live collection."""
        logging.debug("Snapshotting...")

        table = await self.get_table(_LIVE_COLLECTION)
        if not table:
            logging.info("Snapshot aborted -- no previous live collection.")
            return ""

        collection = str(time.time())
        await self._ingest_new_collection(collection, table)

        logging.info(f"Snapshotted {collection}.")
        return collection

    async def list_snapshot_timestamps(self) -> List[str]:
        """Return a list of the snapshot collections."""
        logging.info("Getting Snapshot Timestamps...")

        snapshots = [
            c for c in await self._list_collection_names() if c != _LIVE_COLLECTION
        ]

        logging.debug(f"Snapshot Timestamps {snapshots}.")
        return snapshots

    async def restore_record(self, id_: str) -> None:
        """Mark the record as not deleted."""
        logging.debug(f"Restoring {id_}...")

        query = self._mongofy_record({tc.ID: id_})
        record = await self._get_collection(_LIVE_COLLECTION).find_one(query)
        record.update({IS_DELETED: False})
        record = await self.upsert_record(record)

        logging.info(f"Restored {id_}.")
