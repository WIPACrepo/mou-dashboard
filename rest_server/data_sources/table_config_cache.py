"""Interface for retrieving values for the table config."""


import dataclasses as dc
import logging
import time
from typing import Final

import universal_utils.types as uut

from . import columns, todays_institutions, wbs

US = "US"
NON_US = "Non-US"


@dc.dataclass(frozen=True)
class _ColumnConfig:
    """For column configs."""

    width: int

    tooltip: str = ""
    non_editable: bool = False
    hidden: bool = False
    mandatory: bool = False
    options: list[str] | None = None
    sort_value: int | None = None
    conditional_parent: str | None = None
    conditional_options: dict[str, list[str]] | None = None
    border_left: bool = False
    on_the_fly: bool = False
    numeric: bool = False


_LABOR_CATEGORY_DICTIONARY: dict[str, str] = {
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


_TASK_CATEGORY_DICTIONARY: dict[str, str] = {
    "Standard": "",
    "Intro": "",
    "Open": "",
    "Custom": "",
}

MAX_CACHE_AGE = 60 * 60  # seconds


class TableConfigCache:
    """Manage the collection and parsing of the table config."""

    @staticmethod
    async def create() -> "TableConfigCache":
        """Factory function."""
        # pylint:disable=protected-access
        column_configs, institutions = await TableConfigCache._build()
        new = TableConfigCache(column_configs, institutions)
        return new

    def __init__(
        self,
        _column_configs: dict[str, _ColumnConfig],
        _institutions: list[todays_institutions.Institution],
    ) -> None:
        self.column_configs, self.institutions = _column_configs, _institutions
        self._timestamp = int(time.time())

    async def refresh(self) -> None:
        """Get/Create the most recent table-config doc."""
        if int(time.time()) - self._timestamp < MAX_CACHE_AGE:
            return
        self.column_configs, self.institutions = await self._build()
        self._timestamp = int(time.time())

    @staticmethod
    async def _build() -> tuple[
        dict[str, _ColumnConfig], list[todays_institutions.Institution]
    ]:
        """Build the table config."""
        tooltip_funding_source_value: Final[str] = (
            "This number is dependent on the Funding Source and FTE. "
            "Changing those values will affect this number."
        )

        institutions = await todays_institutions.request_krs_institutions()
        logging.debug(f"KRS responded with {len(institutions)} institutions")

        # build column-configs
        column_configs: Final[dict[str, _ColumnConfig]] = {
            columns.WBS_L2: _ColumnConfig(
                width=115,
                sort_value=70,
                tooltip="WBS Level 2 Category",
                mandatory=True,
            ),
            columns.WBS_L3: _ColumnConfig(
                width=115,
                sort_value=60,
                tooltip="WBS Level 3 Category",
                mandatory=True,
            ),
            columns.US_NON_US: _ColumnConfig(
                width=50,
                non_editable=True,
                hidden=True,
                border_left=True,
                on_the_fly=True,
                sort_value=50,
                tooltip="The institution's region. This cannot be changed.",
            ),
            columns.INSTITUTION: _ColumnConfig(
                width=70,
                options=sorted(set(inst.short_name for inst in institutions)),
                border_left=True,
                sort_value=40,
                tooltip="The institution. This cannot be changed.",
                mandatory=True,
            ),
            columns.LABOR_CAT: _ColumnConfig(
                width=50,
                options=sorted(_LABOR_CATEGORY_DICTIONARY.keys()),
                sort_value=30,
                tooltip="The labor category",
                mandatory=True,
            ),
            columns.NAME: _ColumnConfig(
                width=100,
                sort_value=20,
                tooltip="LastName, FirstName",
                mandatory=True,
            ),
            columns.TASK: _ColumnConfig(
                width=75,
                sort_value=25,
                options=sorted(_TASK_CATEGORY_DICTIONARY.keys()),
                tooltip="Task category",
                # TODO: remove when task category is enabled in future release
                mandatory=False,  # make True?
                non_editable=True,
                hidden=True,
            ),
            columns.TASK_DESCRIPTION: _ColumnConfig(
                width=200,
                tooltip="A description of the task",
            ),
            columns.SOURCE_OF_FUNDS_US_ONLY: _ColumnConfig(
                width=100,
                conditional_parent=columns.US_NON_US,
                conditional_options={
                    US: [
                        columns.NSF_MO_CORE,
                        columns.NSF_BASE_GRANTS,
                        columns.US_IN_KIND,
                    ],
                    NON_US: [columns.NON_US_IN_KIND],
                },
                border_left=True,
                sort_value=10,
                tooltip="The funding source",
                mandatory=True,
            ),
            columns.FTE: _ColumnConfig(
                width=50,
                numeric=True,
                tooltip="FTE for funding source",
                mandatory=True,
            ),
            columns.TOTAL_COL: _ColumnConfig(
                width=100,
                non_editable=True,
                hidden=True,
                border_left=True,
                on_the_fly=True,
                tooltip="TOTAL-ROWS ONLY: FTE totals to the right refer to this category.",
            ),
            columns.NSF_MO_CORE: _ColumnConfig(
                width=50,
                non_editable=True,
                hidden=True,
                numeric=True,
                on_the_fly=True,
                tooltip=tooltip_funding_source_value,
            ),
            columns.NSF_BASE_GRANTS: _ColumnConfig(
                width=50,
                non_editable=True,
                hidden=True,
                numeric=True,
                on_the_fly=True,
                tooltip=tooltip_funding_source_value,
            ),
            columns.US_IN_KIND: _ColumnConfig(
                width=50,
                non_editable=True,
                hidden=True,
                numeric=True,
                on_the_fly=True,
                tooltip=tooltip_funding_source_value,
            ),
            columns.NON_US_IN_KIND: _ColumnConfig(
                width=50,
                non_editable=True,
                hidden=True,
                numeric=True,
                on_the_fly=True,
                tooltip=tooltip_funding_source_value,
            ),
            columns.GRAND_TOTAL: _ColumnConfig(
                width=50,
                numeric=True,
                non_editable=True,
                hidden=True,
                border_left=True,
                on_the_fly=True,
                tooltip="This is is the total of the four FTEs to the left.",
            ),
            columns.ID: _ColumnConfig(
                width=0,
                non_editable=True,
                border_left=True,
                hidden=True,
            ),
            columns.TIMESTAMP: _ColumnConfig(
                width=100,
                non_editable=True,
                border_left=True,
                hidden=True,
                tooltip=f"{columns.TIMESTAMP} (you may need to refresh to reflect a recent update)",
            ),
            columns.EDITOR: _ColumnConfig(
                width=100,
                non_editable=True,
                hidden=True,
                tooltip=f"{columns.EDITOR} (you may need to refresh to reflect a recent update)",
            ),
        }

        return column_configs, institutions

    def us_or_non_us(self, inst_name: str) -> str:
        """Return "US" or "Non-US" per institution name."""
        for inst in self.institutions:
            if inst.short_name == inst_name:
                if inst.is_us:
                    return US
                return NON_US
        return ""

    def get_columns(self) -> list[str]:
        """Get the columns."""
        return list(self.column_configs.keys())

    def get_labor_categories_and_abbrevs(self) -> list[tuple[str, str]]:
        """Get the labor categories and their abbreviations."""
        return [(name, abbrev) for abbrev, name in _LABOR_CATEGORY_DICTIONARY.items()]

    @staticmethod
    def get_l2_categories(l1: str) -> list[str]:
        """Get the L2 categories."""
        return list(wbs.WORK_BREAKDOWN_STRUCTURES[l1].keys())

    @staticmethod
    def get_l3_categories_by_l2(l1: str, l2: str) -> list[str]:
        """Get the L3 categories for an L2 value."""
        return wbs.WORK_BREAKDOWN_STRUCTURES[l1][l2]

    def get_simple_dropdown_menus(self, l1: str) -> dict[str, list[str]]:
        """Get the columns that are simple dropdowns, with their options."""
        ret = {
            col: config.options
            for col, config in self.column_configs.items()
            if config.options
        }
        ret[columns.WBS_L2] = self.get_l2_categories(l1)
        return ret

    def get_conditional_dropdown_menus(
        self, l1: str
    ) -> dict[str, tuple[str, dict[str, list[str]]]]:
        """Get the columns (and conditions) that are conditionally dropdowns.

        Example:
        {'Col-Name-A' : ('Parent-Col-Name-1', {'Parent-Val-I' : ['Option-Alpha', ...] } ) }
        """
        ret = {
            col: (config.conditional_parent, config.conditional_options)
            for col, config in self.column_configs.items()
            if config.conditional_parent and config.conditional_options
        }
        ret[columns.WBS_L3] = (columns.WBS_L2, wbs.WORK_BREAKDOWN_STRUCTURES[l1])
        return ret

    def get_dropdowns(self, l1: str) -> list[str]:
        """Get the columns that are dropdowns."""
        return list(self.get_simple_dropdown_menus(l1).keys()) + list(
            self.get_conditional_dropdown_menus(l1).keys()
        )

    def get_numerics(self) -> list[str]:
        """Get the columns that have numeric data."""
        return [col for col, config in self.column_configs.items() if config.numeric]

    def get_non_editables(self) -> list[str]:
        """Get the columns that are not editable."""
        return [
            col for col, config in self.column_configs.items() if config.non_editable
        ]

    def get_hiddens(self) -> list[str]:
        """Get the columns that are hidden."""
        return [col for col, config in self.column_configs.items() if config.hidden]

    def get_mandatory_columns(self) -> list[str]:
        """Get the columns that are hidden."""
        return [col for col, config in self.column_configs.items() if config.mandatory]

    def get_widths(self) -> dict[str, int]:
        """Get the widths of each column."""
        return {col: config.width for col, config in self.column_configs.items()}

    def get_tooltips(self) -> dict[str, str]:
        """Get the widths of each column."""
        return {
            col: config.tooltip
            for col, config in self.column_configs.items()
            if config.tooltip
        }

    def get_border_left_columns(self) -> list[str]:
        """Get the columns that have a left border."""
        return [
            col for col, config in self.column_configs.items() if config.border_left
        ]

    def get_page_size(self) -> int:
        """Get page size."""
        return 19

    def get_on_the_fly_fields(self) -> list[str]:
        """Get names of fields created on-the-fly, data not stored."""
        return [col for col, config in self.column_configs.items() if config.on_the_fly]

    def sort_key(self, k: dict[str, uut.DataEntry]) -> tuple[uut.DataEntry, ...]:
        """Sort key for the table."""
        sort_keys: list[uut.DataEntry] = []

        column_orders = {
            col: config.sort_value
            for col, config in self.column_configs.items()
            if config.sort_value
        }
        columns_by_precedence = sorted(
            column_orders.keys(), key=lambda x: column_orders[x], reverse=True
        )

        for col in columns_by_precedence:
            sort_keys.append(k.get(col, "ZZZZ"))  # HACK: sort empty/missing values last

        return tuple(sort_keys)
