"""Database utilities."""

import asyncio
import pprint
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


class NoCollectionsFoundError(Exception):
    """Raise if there are no collections meeting conditions."""


class MoUMotorClient:
    """MotorClient with additional guardrails for MoU things."""

    def __init__(self, motor_client: MotorClient, xlsx: str = "") -> None:
        self._client = motor_client

        def _run(f: Coroutine[Any, Any, Any]) -> Any:
            return asyncio.get_event_loop().run_until_complete(f)

        # ingest xlsx
        if xlsx:
            collection = _run(self._ingest_xlsx(xlsx))
            pprint.pprint(_run(self.get_table(collection)))

        # check indexes
        _run(self._ensure_all_databases_indexes())

    @staticmethod
    def _mongofy_key_name(key: str) -> str:
        return key.replace(".", ";")

    @staticmethod
    def _demongofy_key_name(key: str) -> str:
        return key.replace(";", ".")

    @staticmethod
    def _mongofy_record(record: Record) -> Record:
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
        if record.get(IS_DELETED):
            record.pop(IS_DELETED)

        return record

    async def _ingest_xlsx(self, xlsx: str) -> str:
        """Create a collection and ingest the xlsx's data."""
        collection = str(int(time.time()))
        coll_obj = await self._create_collection(collection)

        def _is_a_total_row(row: Record) -> bool:
            for data in row.values():
                if isinstance(data, str) and ("TOTAL" in data.upper()):
                    return True
            return False

        # read data from excel file
        # remove blanks and rows with "total" in them (case-insensitive)
        table: Table = [
            self._mongofy_record(row)
            for row in pd.read_excel(xlsx).fillna("").to_dict("records")
            if any(row.values()) and not _is_a_total_row(row)
        ]

        # ingest
        await coll_obj.insert_many(table)

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

    async def list_collection_names(self, db: str = SNAPSHOTS_DB) -> List[str]:
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

    async def _create_collection(
        self, collection: str, db: str = SNAPSHOTS_DB
    ) -> MotorCollection:
        """Return collection instance, if it doesn't exist, create it."""
        db_obj = self._get_db(db)
        try:
            return db_obj[collection]
        except KeyError:
            coll_obj = db_obj.create_collection(collection)
            await self._ensure_collection_indexes(collection, db)
            return coll_obj

    async def _ensure_collection_indexes(
        self, collection: str, db: str = SNAPSHOTS_DB
    ) -> None:
        """Create indexes in collection."""
        coll_obj = self._get_collection(collection, db)

        # _id = self._mongofy_key_name(tc.ID)
        # await coll_obj.create_index(_id, name=f"{_id}_index", unique=True)

        _inst = self._mongofy_key_name(tc.INSTITUTION)
        await coll_obj.create_index(_inst, name=f"{_inst}_index", unique=False)

        _labor = self._mongofy_key_name(tc.LABOR_CAT)
        await coll_obj.create_index(_labor, name=f"{_labor}_index", unique=False)

        async for index in coll_obj.list_indexes():
            print(index)

    async def _ensure_all_databases_indexes(self) -> None:
        """Create all indexes in all databases."""
        for db in await self._list_database_names():
            for collection in await self.list_collection_names(db):
                await self._ensure_collection_indexes(collection, db)

    async def most_recent_collection(self) -> str:
        """Get the most recently created collection.

        Collections are named with the Unix epoch. Raise
        NoCollectionsFoundError if no collections are found.
        """
        timestamps = [int(c) for c in await self.list_collection_names()]
        try:
            return str(max(timestamps))
        except ValueError:
            raise NoCollectionsFoundError

    async def get_table(
        self, collection: str = "", labor: str = "", institution: str = ""
    ) -> Table:
        """Return the table from the collection name."""
        if not collection:
            try:
                collection = await self.most_recent_collection()
            except NoCollectionsFoundError:
                print("NoCollectionsFoundError")
                return []

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

        print(
            f"Table ({institution=}, {labor=}) has {i} records (and {dels} deleted records)."
        )
        return table

    async def upsert_record(self, record: Record, collection: str = "") -> Record:
        """Insert a record.

        Update if it already exists.
        """
        record = self._mongofy_record(record)

        if not collection:
            try:
                collection = await self.most_recent_collection()
            except NoCollectionsFoundError:
                return {}
        collection_obj = self._get_collection(collection)

        # if record has an ID -- replace it
        if record.get(tc.ID):
            res = await collection_obj.replace_one({tc.ID: record[tc.ID]}, record)
            print(f"Updated {record}")
        # otherwise -- create it
        else:
            record.pop(tc.ID)
            res = await collection_obj.insert_one(record)
            record[tc.ID] = res.inserted_id
            print(f"Inserted {record}")

        return self._demongofy_record(record)

    async def delete_record(self, record: Record, collection: str = "") -> Record:
        """Mark the record as deleted."""
        record.update({IS_DELETED: True})
        record = await self.upsert_record(record, collection=collection)

        print(f"Deleted {record}")
        return record
