"""Database interface for retrieving values for the table config."""


import asyncio
import copy
import time
from typing import Any, Dict, Final, List, Optional, Tuple, TypedDict, Union, cast

from bson.objectid import ObjectId  # type: ignore[import]
from motor.motor_tornado import MotorClient  # type: ignore

from .. import wbs
from ..utils.mongo_tools import Mongofier

ID = "_id"
WBS_L2 = "WBS L2"
WBS_L3 = "WBS L3"
LABOR_CAT = "Labor Cat."
US_NON_US = "US / Non-US"
INSTITUTION = "Institution"
_NAME = "Name"
TASK_DESCRIPTION = "Task Description"
SOURCE_OF_FUNDS_US_ONLY = "Source of Funds (U.S. Only)"
FTE = "FTE"
NSF_MO_CORE = "NSF M&O Core"
NSF_BASE_GRANTS = "NSF Base Grants"
US_IN_KIND = "US In-Kind"
NON_US_IN_KIND = "Non-US In-Kind"
GRAND_TOTAL = "Grand Total"
TOTAL_COL = "Total-Row Description"
TIMESTAMP = "Date & Time of Last Edit"
EDITOR = "Name of Last Editor"

US = "US"
NON_US = "Non-US"


class InstitutionMeta(TypedDict):  # NOTE: from krs
    """Metadata schema for an institution."""

    cite: str
    abbreviation: str
    is_US: bool
    region: str


class _ColumnConfigTypedDict(TypedDict, total=False):
    """TypedDict for column configs."""

    width: int
    tooltip: str
    non_editable: bool
    hidden: bool
    options: List[str]
    sort_value: int
    conditional_parent: str
    conditional_options: Dict[str, List[str]]
    border_left: bool
    on_the_fly: bool
    funding_source: bool
    numeric: bool


_LABOR_CATEGORY_DICTIONARY: Dict[str, str] = {
    # Science
    "KE": "Key Personnel (Faculty Members)",
    "SC": "Scientist",
    "PO": "Postdoctoral Associates",
    "GR": "Graduate Students (PhD Students)",
    # Technical
    "AD": "Administration",
    "CS": "Computer Science",
    "DS": "Data Science",
    "EN": "Engineering",
    "IT": "Information Technology",
    "MA": "Manager",
    "WO": "Winterover",
}

MAX_CACHE_AGE = 60 * 60  # seconds
DB_NAME = "table_config"
COLLECTION_NAME = "cache"


def krs_institution_dicts() -> Dict[str, InstitutionMeta]:
    """Grab the master list of institutions along with their details.

    NOTE: locally importing is a stopgap measure until
    the Keycloak REST Service is operational.
    """
    # TODO: remove when krs is up and running
    from .institution_list import (  # type: ignore[import]  # pylint:disable=C0415,E0401
        ICECUBE_INSTS,
    )

    return ICECUBE_INSTS  # type: ignore


class _TableConfigDoc(TypedDict):
    column_configs: Dict[str, _ColumnConfigTypedDict]
    institution_dicts: Dict[str, InstitutionMeta]
    timestamp: int


class TableConfigDatabaseClient:
    """Manage the collection and parsing of the table config(s)."""

    def __init__(self, motor_client: MotorClient) -> None:
        self._mongo = motor_client
        self._doc = None
        self._doc = asyncio.get_event_loop().run_until_complete(self.refresh_doc())

    def column_configs(self) -> Dict[str, _ColumnConfigTypedDict]:
        """The column-config dicts."""
        doc = asyncio.get_event_loop().run_until_complete(self.refresh_doc())
        return doc["column_configs"]

    def institution_dicts(self) -> Dict[str, InstitutionMeta]:
        """The institution dicts."""
        doc = asyncio.get_event_loop().run_until_complete(self.refresh_doc())
        return doc["institution_dicts"]

    async def get_most_recent_doc(
        self,
    ) -> Tuple[Optional[_TableConfigDoc], Optional[ObjectId]]:
        """Get doc w/ largest timestamp value, also its mongo id."""
        cursor = self._mongo[DB_NAME][COLLECTION_NAME].find()
        cursor.sort("timestamp", -1).limit(1)
        async for doc in cursor:
            doc = Mongofier.demongofy_document(doc, str_id=False)
            return cast(_TableConfigDoc, doc), doc.pop(ID)
        return None, None

    async def _insert_replace(
        self, doc: _TableConfigDoc, _id: Optional[ObjectId] = None
    ) -> None:
        """Insert `doc` into db. If passed `_id`, replace existing doc."""
        doc = Mongofier.mongofy_document(doc)  # type: ignore[arg-type, assignment]
        if _id:
            await self._mongo[DB_NAME][COLLECTION_NAME].replace_one({"_id": _id}, doc)
        else:
            await self._mongo[DB_NAME][COLLECTION_NAME].insert_one(doc)

    async def refresh_doc(self) -> _TableConfigDoc:
        """Get the most recent table-config doc."""
        if self._doc and int(time.time()) - self._doc["timestamp"] < MAX_CACHE_AGE:
            return self._doc

        def doc_has_changed(from_db: _TableConfigDoc, newest: _TableConfigDoc) -> bool:
            for field in newest.keys():
                if field in ["timestamp"]:
                    continue
                if newest[field] != from_db[field]:  # type: ignore[misc]
                    return True
            return False

        # Handle inserting/updating
        from_db, from_db_id = await self.get_most_recent_doc()
        if from_db:
            newest = self.build_table_config_doc(from_db)
            # Insert, if data has changed
            if doc_has_changed(from_db, newest):
                await self._insert_replace(newest)
            # Otherwise, just update what's already in there
            else:
                await self._insert_replace(newest, from_db_id)
        # Otherwise, the db is empty!
        else:
            newest = self.build_table_config_doc(None)
            await self._insert_replace(newest)

        self._doc = newest
        return self._doc

    @staticmethod
    def build_table_config_doc(prev_doc: Optional[_TableConfigDoc]) -> _TableConfigDoc:
        """Build the table config doc.

        If an actual `prev_doc` is passed, then incorporate
        the institutions into the out doc. This is needed to
        preserve institutions that are no longer in krs, but
        are in previous MoUs.

        NOTE: future development can incorporate more from
        `prev_doc` (like `col_widths`) and process similarly.
        """
        tooltip_funding_source_value: Final[str] = (
            "This number is dependent on the Funding Source and FTE. "
            "Changing those values will affect this number."
        )

        # aggregate institution dicts
        institution_dicts = {}
        if prev_doc:
            institution_dicts = copy.deepcopy(prev_doc["institution_dicts"])
        institution_dicts.update(krs_institution_dicts())

        # build column-configs
        column_configs: Final[Dict[str, _ColumnConfigTypedDict]] = {
            WBS_L2: {"width": 115, "sort_value": 70, "tooltip": "WBS Level 2 Category"},
            WBS_L3: {"width": 115, "sort_value": 60, "tooltip": "WBS Level 3 Category"},
            US_NON_US: {
                "width": 50,
                "non_editable": True,
                "hidden": True,
                "border_left": True,
                "on_the_fly": True,
                "sort_value": 50,
                "tooltip": "The institution's region. This cannot be changed.",
            },
            INSTITUTION: {
                "width": 70,
                "options": sorted(
                    set(inst["abbreviation"] for inst in institution_dicts.values())
                ),
                "border_left": True,
                "sort_value": 40,
                "tooltip": "The institution. This cannot be changed.",
            },
            LABOR_CAT: {
                "width": 50,
                "options": sorted(_LABOR_CATEGORY_DICTIONARY.keys()),
                "sort_value": 30,
                "tooltip": "The labor category",
            },
            _NAME: {"width": 100, "sort_value": 20, "tooltip": "LastName, FirstName"},
            TASK_DESCRIPTION: {"width": 300, "tooltip": "A description of the task"},
            SOURCE_OF_FUNDS_US_ONLY: {
                "width": 100,
                "conditional_parent": US_NON_US,
                "conditional_options": {
                    US: [NSF_MO_CORE, NSF_BASE_GRANTS, US_IN_KIND],
                    NON_US: [NON_US_IN_KIND],
                },
                "border_left": True,
                "sort_value": 10,
                "tooltip": "The funding source",
            },
            FTE: {"width": 50, "numeric": True, "tooltip": "FTE for funding source"},
            TOTAL_COL: {
                "width": 100,
                "non_editable": True,
                "hidden": True,
                "border_left": True,
                "on_the_fly": True,
                "tooltip": "TOTAL-ROWS ONLY: FTE totals to the right refer to this category.",
            },
            NSF_MO_CORE: {
                "width": 50,
                "funding_source": True,
                "non_editable": True,
                "hidden": True,
                "numeric": True,
                "on_the_fly": True,
                "tooltip": tooltip_funding_source_value,
            },
            NSF_BASE_GRANTS: {
                "width": 50,
                "funding_source": True,
                "non_editable": True,
                "hidden": True,
                "numeric": True,
                "on_the_fly": True,
                "tooltip": tooltip_funding_source_value,
            },
            US_IN_KIND: {
                "width": 50,
                "funding_source": True,
                "non_editable": True,
                "hidden": True,
                "numeric": True,
                "on_the_fly": True,
                "tooltip": tooltip_funding_source_value,
            },
            NON_US_IN_KIND: {
                "width": 50,
                "funding_source": True,
                "non_editable": True,
                "hidden": True,
                "numeric": True,
                "on_the_fly": True,
                "tooltip": tooltip_funding_source_value,
            },
            GRAND_TOTAL: {
                "width": 50,
                "numeric": True,
                "non_editable": True,
                "hidden": True,
                "border_left": True,
                "on_the_fly": True,
                "tooltip": "This is is the total of the four FTEs to the left.",
            },
            ID: {"width": 0, "non_editable": True, "border_left": True, "hidden": True},
            TIMESTAMP: {
                "width": 100,
                "non_editable": True,
                "border_left": True,
                "hidden": True,
                "tooltip": f"{TIMESTAMP} (you may need to refresh to reflect a recent update)",
            },
            EDITOR: {
                "width": 100,
                "non_editable": True,
                "hidden": True,
                "tooltip": f"{EDITOR} (you may need to refresh to reflect a recent update)",
            },
        }

        return {
            "column_configs": column_configs,
            "institution_dicts": institution_dicts,
            "timestamp": int(time.time()),
        }

    def us_or_non_us(self, institution: str) -> str:
        """Return "US" or "Non-US" per institution name."""
        for inst in self.institution_dicts().values():
            if inst["abbreviation"] == institution:
                if inst["is_US"]:
                    return US
                return NON_US
        return ""

    def get_columns(self) -> List[str]:
        """Get the columns."""
        return list(self.column_configs().keys())

    def get_institutions_and_abbrevs(self) -> List[Tuple[str, str]]:
        """Get the institutions and their abbreviations."""
        abbrev_name: Dict[str, str] = {}
        for inst, val in self.institution_dicts().items():
            # for institutions with the same abbreviation (aka different departments)
            # append their name
            if val["abbreviation"] in abbrev_name:
                abbrev_name[
                    val["abbreviation"]
                ] = f"{abbrev_name[val['abbreviation']]} / {inst}"
            else:
                abbrev_name[val["abbreviation"]] = inst

        return [(name, abbrev) for abbrev, name in abbrev_name.items()]

    def get_labor_categories_and_abbrevs(self) -> List[Tuple[str, str]]:
        """Get the labor categories and their abbreviations."""
        return [(name, abbrev) for abbrev, name in _LABOR_CATEGORY_DICTIONARY.items()]

    @staticmethod
    def get_l2_categories(l1: str) -> List[str]:
        """Get the L2 categories."""
        return list(wbs.WORK_BREAKDOWN_STRUCTURES[l1].keys())

    @staticmethod
    def get_l3_categories_by_l2(l1: str, l2: str) -> List[str]:
        """Get the L3 categories for an L2 value."""
        return wbs.WORK_BREAKDOWN_STRUCTURES[l1][l2]

    def get_simple_dropdown_menus(self, l1: str) -> Dict[str, List[str]]:
        """Get the columns that are simple dropdowns, with their options."""
        ret = {
            col: config["options"]
            for col, config in self.column_configs().items()
            if "options" in config
        }
        ret[WBS_L2] = self.get_l2_categories(l1)
        return ret

    def get_conditional_dropdown_menus(
        self, l1: str
    ) -> Dict[str, Tuple[str, Dict[str, List[str]]]]:
        """Get the columns (and conditions) that are conditionally dropdowns.

        Example:
        {'Col-Name-A' : ('Parent-Col-Name-1', {'Parent-Val-I' : ['Option-Alpha', ...] } ) }
        """
        ret = {
            col: (config["conditional_parent"], config["conditional_options"])
            for col, config in self.column_configs().items()
            if ("conditional_parent" in config) and ("conditional_options" in config)
        }
        ret[WBS_L3] = (WBS_L2, wbs.WORK_BREAKDOWN_STRUCTURES[l1])
        return ret

    def get_dropdowns(self, l1: str) -> List[str]:
        """Get the columns that are dropdowns."""
        return list(self.get_simple_dropdown_menus(l1).keys()) + list(
            self.get_conditional_dropdown_menus(l1).keys()
        )

    def get_numerics(self) -> List[str]:
        """Get the columns that have numeric data."""
        return [
            col
            for col, config in self.column_configs().items()
            if config.get("numeric")
        ]

    def get_non_editables(self) -> List[str]:
        """Get the columns that are not editable."""
        return [
            col
            for col, config in self.column_configs().items()
            if config.get("non_editable")
        ]

    def get_hiddens(self) -> List[str]:
        """Get the columns that are hidden."""
        return [
            col for col, config in self.column_configs().items() if config.get("hidden")
        ]

    def get_widths(self) -> Dict[str, int]:
        """Get the widths of each column."""
        return {col: config["width"] for col, config in self.column_configs().items()}

    def get_tooltips(self) -> Dict[str, str]:
        """Get the widths of each column."""
        return {
            col: config["tooltip"]
            for col, config in self.column_configs().items()
            if config.get("tooltip")
        }

    def get_border_left_columns(self) -> List[str]:
        """Get the columns that have a left border."""
        return [
            col
            for col, config in self.column_configs().items()
            if config.get("border_left")
        ]

    def get_page_size(self) -> int:  # pylint: disable=no-self-use
        """Get page size."""
        return 19

    def get_on_the_fly_fields(self) -> List[str]:
        """Get names of fields created on-the-fly, data not stored."""
        return [
            col
            for col, config in self.column_configs().items()
            if config.get("on_the_fly")
        ]

    def sort_key(self, k: Dict[str, Union[int, float, str]]) -> Tuple[Any, ...]:
        """Sort key for the table."""
        sort_keys: List[Union[int, float, str]] = []

        column_orders = {
            col: config["sort_value"]
            for col, config in self.column_configs().items()
            if "sort_value" in config
        }
        columns_by_precedence = sorted(
            column_orders.keys(), key=lambda x: column_orders[x], reverse=True
        )

        for col in columns_by_precedence:
            sort_keys.append(k.get(col, "ZZZZ"))  # HACK: sort empty/missing values last

        return tuple(sort_keys)
