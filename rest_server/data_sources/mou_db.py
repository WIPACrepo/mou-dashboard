"""Database interface for MOU data."""

import base64
import dataclasses as dc
import io
import logging
import time
from typing import cast

import dacite
import pandas as pd  # type: ignore[import]
import pymongo.errors
import universal_utils.types as uut
from motor.motor_tornado import MotorClient  # type: ignore
from tornado import web

from ..config import EXCLUDE_COLLECTIONS, EXCLUDE_DBS
from ..utils import types, utils
from ..utils.mongo_tools import DocumentNotFoundError, Mongofier
from . import columns

LIVE_COLLECTION = "LIVE_COLLECTION"


class MOUDatabaseClient:
    """MotorClient with additional guardrails for MOU things."""

    def __init__(
        self, motor_client: MotorClient, data_adaptor: utils.MOUDataAdaptor
    ) -> None:
        self.data_adaptor = data_adaptor
        self._mongo = motor_client

    async def _override_live_collection_for_xlsx(  # pylint: disable=R0913
        self,
        wbs_db: str,
        table: uut.DBTable,
        creator: str,
        all_insts_values: dict[str, uut.InstitutionValues],
    ) -> None:
        """Create the live collection."""
        logging.debug(f"Creating Live Collection ({wbs_db=})...")

        for record in table:
            record.update({columns.EDITOR: "", columns.TIMESTAMP: time.time()})

        await self._ingest_new_collection(
            wbs_db,
            LIVE_COLLECTION,
            table,
            "",
            creator,
            all_insts_values,
            False,
            confirmation_touchstone_ts=0,
        )

        logging.debug(f"Created Live Collection: ({wbs_db=}) {len(table)} records.")

    async def ingest_xlsx(  # pylint:disable=too-many-locals
        self, wbs_db: str, base64_xlsx: str, filename: str, creator: str
    ) -> tuple[str, str]:
        """Ingest the xlsx's data as the new Live Collection.

        Also make snapshots of the previous live table and the new one.
        """
        logging.info(f"Ingesting xlsx {filename} ({wbs_db=})...")

        def _is_a_total_row(row: uut.DBRecord) -> bool:
            # check L2, L3, Inst., & US/Non-US  columns for "total" substring
            for key in [
                columns.WBS_L2,
                columns.WBS_L3,
                columns.INSTITUTION,
                columns.US_NON_US,
            ]:
                data = row.get(key)
                if isinstance(data, str) and ("TOTAL" in data.upper()):
                    return True
            return False

        def _row_has_data(row: uut.DBRecord) -> bool:
            # check purely blank rows
            if not any(row.values()):  # purely blank rows
                return False
            # check blanks except tc.WBS_L2, tc.WBS_L3, & tc.US_NON_US
            for key, val in row.items():
                if key in [columns.WBS_L2, columns.WBS_L3, columns.US_NON_US]:
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
            raw_table = cast(list[uut.DBRecord], df.fillna("").to_dict("records"))
        except Exception as e:
            raise web.HTTPError(400, reason=str(e))

        # check schema -- aka verify column names
        for row in raw_table:
            # check for extra keys
            if not all(
                k in self.data_adaptor.tc_cache.get_columns() for k in row.keys()
            ):
                raise web.HTTPError(
                    422,
                    reason=f"Table not in correct format: "
                    f"XLSX's KEYS={row.keys()} vs "
                    f"ALLOWABLE KEYS={self.data_adaptor.tc_cache.get_columns()})",
                )

        # mongofy table -- and verify data
        try:
            tc_adaptor = TableConfigDataAdaptor(self.data_adaptor.tc_cache)
            table: uut.DBTable = [
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
            all_insts_values = doc.snapshot_institution_values
        except (DocumentNotFoundError, pymongo.errors.InvalidName):
            all_insts_values = {}
        await self._override_live_collection_for_xlsx(
            wbs_db, table, creator, all_insts_values
        )

        # snapshot
        current_snap = await self.snapshot_live_collection(
            wbs_db, "Initial Import", creator, admin_only=True
        )

        logging.debug(
            f"Ingested xlsx: {filename=}, {wbs_db=}, {current_snap}, {previous_snap}."
        )
        return previous_snap, current_snap

    async def _list_database_names(self) -> list[str]:
        """Return all databases' names."""
        return [
            n for n in await self._mongo.list_database_names() if n not in EXCLUDE_DBS
        ]

    async def _list_collection_names(self, db: str) -> list[str]:
        """Return collection names in database."""
        return [
            n
            for n in await self._mongo[db].list_collection_names()
            if n not in EXCLUDE_COLLECTIONS
        ]

    async def get_snapshot_info(self, wbs_db: str, snap_coll: str) -> uut.SnapshotInfo:
        """Get the name of the snapshot."""
        logging.debug(f"Getting Snapshot Name ({wbs_db=}, {snap_coll=})...")

        await self._check_database_state(wbs_db)

        doc = await self._get_supplemental_doc(wbs_db, snap_coll)

        logging.info(f"Snapshot Name [{doc.name}] ({wbs_db=}, {snap_coll=})...")
        return uut.SnapshotInfo(
            name=doc.name,
            creator=doc.creator,
            timestamp=doc.timestamp,
            admin_only=doc.admin_only,
        )

    async def retouchstone(self, wbs_db: str) -> int:
        """Make an updated touchstone timestamp value for all LIVE
        institutions."""
        logging.debug(f"Re-touchstoning ({wbs_db=})...")

        now = int(time.time())

        doc = await self._get_supplemental_doc(wbs_db, LIVE_COLLECTION)
        doc = dc.replace(doc, confirmation_touchstone_ts=now)
        await self._set_supplemental_doc(wbs_db, LIVE_COLLECTION, doc)

        logging.info(f"Re-touchstoned ({wbs_db=}, {now=}).")
        return now

    async def get_touchstone(self, wbs_db: str) -> int:
        """Get touchstone timestamp value for all LIVE institutions."""
        logging.debug(f"Getting touchstone ({wbs_db=})...")

        try:
            doc = await self._get_supplemental_doc(wbs_db, LIVE_COLLECTION)
        except DocumentNotFoundError:
            return 0

        logging.info(f"Got touchstone ({wbs_db=}, {doc.confirmation_touchstone_ts=}).")
        return doc.confirmation_touchstone_ts

    async def _update_institution_values(
        self,
        wbs_db: str,
        institution: str,
        vals: uut.InstitutionValues,
        snapshot_timestamp: str,
    ) -> uut.InstitutionValues:
        """Put in DB."""
        doc = await self._get_supplemental_doc(wbs_db, snapshot_timestamp)
        doc.snapshot_institution_values.update({institution: dc.asdict(vals)})
        await self._set_supplemental_doc(wbs_db, snapshot_timestamp, doc)

        return vals

    async def confirm_institution_values(
        self,
        wbs_db: str,
        institution: str,
        headcounts: bool,
        table: bool,
        computing: bool,
    ) -> uut.InstitutionValues:
        """Confirm the indicated values for an institution."""
        logging.debug(
            f"Confirming Institution's Values ({wbs_db=}, {institution=}, {headcounts=}, {table=}, {computing=})..."
        )

        await self._check_database_state(wbs_db)

        # update
        vals = await self.get_institution_values(wbs_db, LIVE_COLLECTION, institution)
        vals = vals.confirm(headcounts, table, computing)

        # put in DB
        await self._update_institution_values(
            wbs_db, institution, vals, LIVE_COLLECTION
        )

        logging.info(
            f"Confirmed Institution's Values ({wbs_db=}, {institution=}, {vals=})."
        )
        return vals

    async def upsert_institution_values(
        self,
        wbs_db: str,
        institution: str,
        phds_authors: int | None,
        faculty: int | None,
        scientists_post_docs: int | None,
        grad_students: int | None,
        cpus: int | None,
        gpus: int | None,
        text: str,
    ) -> uut.InstitutionValues:
        """Upsert the values for an institution."""
        logging.debug(
            f"Upserting Institution's Values ({wbs_db=}, {institution=}, {[phds_authors,faculty,scientists_post_docs,grad_students,cpus,gpus,text]=})..."
        )

        await self._check_database_state(wbs_db)

        # update "last edit"s by diffing
        before = await self.get_institution_values(wbs_db, LIVE_COLLECTION, institution)
        vals = before.compute_last_edits(
            phds_authors,
            faculty,
            scientists_post_docs,
            grad_students,
            cpus,
            gpus,
            text,
        )

        # put in DB
        await self._update_institution_values(
            wbs_db, institution, vals, LIVE_COLLECTION
        )

        logging.info(
            f"Upserted Institution's Values ({wbs_db=}, {institution=}, {vals=})."
        )
        return vals

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
    ) -> uut.InstitutionValues:
        """Get the values for an institution."""
        logging.debug(f"Getting Institution's Values ({wbs_db=}, {institution=})...")
        if not snapshot_timestamp:
            raise web.HTTPError(422, reason="collection (snapshot) cannot be falsy")

        while True:
            try:
                return await self._get_institution_values(
                    wbs_db, snapshot_timestamp, institution
                )
            except KeyError:
                # if the inst is missing, make it
                logging.info(
                    f"Creating new institution values ({wbs_db=}, {institution=})..."
                )
                await self._update_institution_values(
                    wbs_db, institution, uut.InstitutionValues(), LIVE_COLLECTION
                )

    async def _get_institution_values(
        self,
        wbs_db: str,
        snapshot_timestamp: str,
        institution: str,
    ) -> uut.InstitutionValues:
        await self._check_database_state(wbs_db)
        if not snapshot_timestamp:
            raise web.HTTPError(422, reason="collection (snapshot) cannot be falsy")

        try:
            doc = await self._get_supplemental_doc(wbs_db, snapshot_timestamp)
        except DocumentNotFoundError as e:
            logging.warning(str(e))
            return uut.InstitutionValues()

        vals = dacite.from_dict(
            uut.InstitutionValues, doc.snapshot_institution_values[institution]
        )
        logging.info(f"Institution's Values [{vals}] ({wbs_db=}, {institution=}).")
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

        supplemental_doc = types.SupplementalDoc(**doc)

        # always override all `confirmation_touchstone_ts` attrs
        supplemental_doc.override_all_institutions_touchstones()

        return supplemental_doc

    async def _set_supplemental_doc(
        self, wbs_db: str, snap_coll: str, doc: types.SupplementalDoc
    ) -> None:
        """Insert/update a Supplemental document."""
        if snap_coll != doc.timestamp:
            raise web.HTTPError(
                400,
                reason=f"Tried to set erroneous supplemental document: {snap_coll=}, {doc=}",
            )

        coll_obj = self._mongo[f"{wbs_db}-supplemental"][snap_coll]
        await coll_obj.replace_one(
            {"timestamp": doc.timestamp}, dc.asdict(doc), upsert=True
        )

    async def _create_supplemental_db_document(  # pylint: disable=R0913
        self,
        wbs_db: str,
        snap_coll: str,
        name: str,
        creator: str,
        all_insts_values: dict[str, uut.InstitutionValues],
        admin_only: bool,
        confirmation_touchstone_ts: int,
    ) -> None:
        logging.debug(f"Creating Supplemental DB/Document ({wbs_db=}, {snap_coll=})...")

        # drop the collection if it already exists
        await self._mongo[f"{wbs_db}-supplemental"].drop_collection(snap_coll)

        # populate the singleton document
        await self._set_supplemental_doc(
            wbs_db,
            snap_coll,
            types.SupplementalDoc(
                name=name,
                timestamp=snap_coll,
                creator=creator,
                snapshot_institution_values={
                    k: dc.asdict(v) for k, v in all_insts_values.items()
                },
                admin_only=admin_only,
                confirmation_touchstone_ts=confirmation_touchstone_ts,
            ),
        )

        logging.debug(
            f"Created Supplemental Document ({wbs_db=}, {snap_coll=}): "
            f"{await self._get_supplemental_doc(wbs_db, snap_coll)}."
        )

    async def _ingest_new_collection(  # pylint: disable=R0913
        self,
        wbs_db: str,
        snap_coll: str,
        table: uut.DBTable,
        name: str,
        creator: str,
        all_insts_values: dict[str, uut.InstitutionValues],
        admin_only: bool,
        confirmation_touchstone_ts: int,
    ) -> None:
        """Add table to a new collection.

        If collection already exists, replace.
        """
        if admin_only and snap_coll == LIVE_COLLECTION:
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
            wbs_db,
            snap_coll,
            name,
            creator,
            all_insts_values,
            admin_only,
            confirmation_touchstone_ts,
        )

    async def _ensure_collection_indexes(self, wbs_db: str, snap_coll: str) -> None:
        """Create indexes in collection."""
        coll_obj = self._mongo[wbs_db][snap_coll]

        _inst = Mongofier.mongofy_key_name(columns.INSTITUTION)
        await coll_obj.create_index(_inst, name=f"{_inst}_index", unique=False)

        _labor = Mongofier.mongofy_key_name(columns.LABOR_CAT)
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
        self, wbs_db: str, snap_coll: str, labor: str, institution: str
    ) -> uut.DBTable:
        """Return the table from the collection name."""
        if not snap_coll:
            raise web.HTTPError(422, reason="collection (snapshot) cannot be falsy")

        logging.debug(f"Getting from {snap_coll} ({wbs_db=})...")

        await self._check_database_state(wbs_db)
        await self._ensure_all_db_indexes()

        query = {}
        if labor:
            query[Mongofier.mongofy_key_name(columns.LABOR_CAT)] = labor
        if institution:
            query[Mongofier.mongofy_key_name(columns.INSTITUTION)] = institution

        # build demongofied table
        table: uut.DBTable = []
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
        self, wbs_db: str, record: uut.DBRecord, editor: str
    ) -> tuple[uut.DBRecord, uut.InstitutionValues | None]:
        """Insert a record.

        Update if it already exists.
        """
        logging.debug(f"Upserting {record} ({wbs_db=})...")

        await self._check_database_state(wbs_db)

        # record timestamp and editor's name
        now = time.time()
        record[columns.TIMESTAMP] = now
        if editor:
            record[columns.EDITOR] = editor

        # prep
        record = self.data_adaptor.mongofy_record(wbs_db, record)
        coll_obj = self._mongo[wbs_db][LIVE_COLLECTION]

        # if record has an ID -- replace it
        if record.get(columns.ID):
            res = await coll_obj.replace_one({columns.ID: record[columns.ID]}, record)
            logging.info(f"Updated {record} ({wbs_db=}) -> {res}.")
        # otherwise -- create it
        else:
            record.pop(columns.ID)
            res = await coll_obj.insert_one(record)
            record[columns.ID] = res.inserted_id
            logging.info(f"Inserted {record} ({wbs_db=}) -> {res}.")

        # update table's last edit in institution values
        instvals = None
        if record[columns.INSTITUTION]:
            instvals = await self.get_institution_values(
                wbs_db,
                LIVE_COLLECTION,
                record[columns.INSTITUTION],  # type: ignore[arg-type]
            )
            instvals = dc.replace(
                instvals,
                table_metadata=dc.replace(
                    instvals.table_metadata, last_edit_ts=int(now)
                ),
            )
            # put in DB
            instvals = await self._update_institution_values(
                wbs_db,
                record[columns.INSTITUTION],  # type: ignore[arg-type]
                instvals,
                LIVE_COLLECTION,
            )

        return self.data_adaptor.demongofy_record(record), instvals

    async def _set_is_deleted_status(
        self, wbs_db: str, record_id: str, is_deleted: bool, editor: str
    ) -> tuple[uut.DBRecord, uut.InstitutionValues | None]:
        """Mark the record as deleted/not-deleted."""
        query = self.data_adaptor.mongofy_record(
            wbs_db,
            {columns.ID: record_id},
        )
        record: uut.DBRecord = await self._mongo[wbs_db][LIVE_COLLECTION].find_one(
            query
        )

        record.update({self.data_adaptor.IS_DELETED: is_deleted})
        record, instvals = await self.upsert_record(wbs_db, record, editor)

        return record, instvals

    async def delete_record(
        self, wbs_db: str, record_id: str, editor: str
    ) -> tuple[uut.DBRecord, uut.InstitutionValues | None]:
        """Mark the record as deleted."""
        logging.debug(f"Deleting {record_id} ({wbs_db=})...")

        await self._check_database_state(wbs_db)

        record, instvals = await self._set_is_deleted_status(
            wbs_db, record_id, True, editor
        )

        logging.info(f"Deleted {record} ({wbs_db=}).")
        return record, instvals

    async def snapshot_live_collection(
        self, wbs_db: str, name: str, creator: str, admin_only: bool
    ) -> str:
        """Create a snapshot collection by copying the live collection."""
        logging.debug(f"Snapshotting ({wbs_db=}, {creator=})...")

        await self._check_database_state(wbs_db)

        table = await self.get_table(wbs_db, LIVE_COLLECTION, "", "")
        supplemental_doc = await self._get_supplemental_doc(wbs_db, LIVE_COLLECTION)

        snap_coll = str(time.time())
        await self._ingest_new_collection(
            wbs_db,
            snap_coll,
            table,
            name,
            creator,
            supplemental_doc.snapshot_institution_values,
            admin_only,
            confirmation_touchstone_ts=supplemental_doc.confirmation_touchstone_ts,
        )

        logging.info(f"Snapshotted {snap_coll} ({wbs_db=}, {creator=}).")
        return snap_coll

    async def _is_snapshot_admin_only(self, wbs_db: str, name: str) -> bool:
        doc = await self._get_supplemental_doc(wbs_db, name)
        return doc.admin_only

    async def list_snapshot_timestamps(
        self, wbs_db: str, exclude_admin_snaps: bool
    ) -> list[str]:
        """Return a list of the snapshot collections.

        NOTE: does not return LIVE_COLLECTION
        """
        logging.info(f"Getting Snapshot Timestamps ({wbs_db=})...")

        await self._check_database_state(wbs_db)

        snapshots = [
            c for c in await self._list_collection_names(wbs_db) if c != LIVE_COLLECTION
        ]
        snapshots.sort(reverse=True)

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

        record = await self._set_is_deleted_status(wbs_db, record_id, False, "")

        logging.info(f"Restored {record} ({wbs_db=}).")
