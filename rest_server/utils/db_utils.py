"""MotorClient with additional guardrails for MoU things."""

from typing import List

from motor.motor_tornado import (  # type: ignore
    MotorClient,
    MotorCollection,
    MotorDatabase,
)
from tornado import web

from ..config import EXCLUDE_DBS


class MoUMotorClient:
    """MotorClient with additional guardrails for MoU things."""

    def __init__(self, motor_client: MotorClient) -> None:
        self.motor_client = motor_client

    async def get_database_names(self) -> List[str]:
        """Return all databases' names."""
        database_names = [
            n
            for n in await self.motor_client.list_database_names()
            if n not in EXCLUDE_DBS
        ]
        return database_names

    def get_database(self, database_name: str) -> MotorDatabase:
        """Return database instance."""
        try:
            return self.motor_client[database_name]
        except (KeyError, TypeError):
            raise web.HTTPError(400, reason=f"database not found ({database_name})")

    async def get_collection_names(self, database_name: str) -> List[str]:
        """Return collection names in database."""
        database = self.get_database(database_name)
        collection_names = [
            n for n in await database.list_collection_names() if n != "system.indexes"
        ]

        return collection_names

    def get_collection(
        self, database_name: str, collection_name: str
    ) -> MotorCollection:
        """Return collection instance."""
        database = self.get_database(database_name)
        try:
            return database[collection_name]
        except KeyError:
            raise web.HTTPError(400, reason=f"collection not found ({collection_name})")

    async def ensure_collection_indexes(
        self, database_name: str, collection_name: str
    ) -> None:
        """Create indexes in collection."""
        collection = self.get_collection(database_name, collection_name)
        await collection.create_index("name", name="name_index", unique=True)
        async for index in collection.list_indexes():
            print(index)

    async def ensure_all_databases_indexes(self) -> None:
        """Create all indexes in all databases."""
        for database_name in await self.get_database_names():
            for collection_name in await self.get_collection_names(database_name):
                await self.ensure_collection_indexes(database_name, collection_name)
