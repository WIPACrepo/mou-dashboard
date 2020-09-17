"""Database utilities."""

import asyncio
from typing import List

import pandas as pd  # type: ignore[import]
from motor.motor_tornado import (  # type: ignore
    MotorClient,
    MotorCollection,
    MotorDatabase,
)
from tornado import web

from .. import table_config as tc
from ..config import EXCLUDE_DBS

DB = "MoUDefaultDB"


class MoUMotorClient:
    """MotorClient with additional guardrails for MoU things."""

    def __init__(self, motor_client: MotorClient, xlsx: str = "") -> None:
        self._client = motor_client

        # ingest xlsx
        if xlsx and not self.list_collections(DB):
            asyncio.get_event_loop().run_until_complete(self._ingest_xlsx(xlsx))

        asyncio.get_event_loop().run_until_complete(self.ensure_all_databases_indexes())

    async def _ingest_xlsx(self, xlsx: str) -> None:
        """Create a collection and ingest the xlsx's data."""
        coll_obj = await self.create_collection(xlsx)

        # read data from excel file
        table = pd.read_excel(xlsx).fillna("")
        table = [r for r in table.to_dict("records") if any(r.values())]
        table = {f"Z{r[tc.ID]}": r for r in table}
        for key in table.keys():
            table[key][tc.ID] = key

        # remove rows with "total" in them (case-insensitive)
        table_copy = {}
        for k, row in table.items():  # pylint: disable=C0103
            # pylint: disable=C0103
            is_a_total_row = False
            for data in row.values():
                if isinstance(data, str) and ("TOTAL" in data.upper()):
                    is_a_total_row = True
            if not is_a_total_row:
                table_copy[k] = row
        table = table_copy

        # ingest
        for record in table:
            await coll_obj.insert_one(record)

    async def _list_dbs(self) -> List[str]:
        """Return all databases' names."""
        return [n for n in await self._client.list_dbs() if n not in EXCLUDE_DBS]

    def _get_db(self, db: str = DB) -> MotorDatabase:
        """Return database instance."""
        try:
            return self._client[db]
        except (KeyError, TypeError):
            raise web.HTTPError(400, reason=f"database not found ({db})")

    async def list_collections(self, db: str = DB) -> List[str]:
        """Return collection names in database."""
        return [
            n
            for n in await self._get_db(db).list_collections()
            if n != "system.indexes"
        ]

    def get_collection(self, collection: str, db: str = DB) -> MotorCollection:
        """Return collection instance."""
        try:
            return self._get_db(db)[collection]
        except KeyError:
            raise web.HTTPError(400, reason=f"collection not found ({collection})")

    async def create_collection(self, collection: str, db: str = DB) -> MotorCollection:
        """Return collection instance, if it doesn't exist, create it."""
        db_obj = self._get_db(db)
        try:
            return db_obj[collection]
        except KeyError:
            coll_obj = db_obj.create_collection(collection)
            await self._ensure_collection_indexes(collection, db)
            return coll_obj

    async def _ensure_collection_indexes(self, collection: str, db: str = DB) -> None:
        """Create indexes in collection."""
        coll_obj = self.get_collection(collection, db)
        await coll_obj.create_index("name", name="name_index", unique=True)
        async for index in coll_obj.list_indexes():
            print(index)

    async def ensure_all_databases_indexes(self) -> None:
        """Create all indexes in all databases."""
        for db in await self._list_dbs():
            for collection in await self.list_collections(db):
                await self._ensure_collection_indexes(collection, db)
