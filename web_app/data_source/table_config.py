"""REST interface for get configurations for the table/columns."""


import dataclasses as dc
import logging
from typing import Final

import cachetools.func

from ..config import MAX_CACHE_MINS
from .connections import mou_request


@dc.dataclass(frozen=True)
class _WBSTableCache:
    """The response dict from '/table/config'."""

    columns: list[str]
    simple_dropdown_menus: dict[str, list[str]]
    labor_categories: list[tuple[str, str]]
    conditional_dropdown_menus: dict[str, tuple[str, dict[str, list[str]]]]
    dropdowns: list[str]
    numerics: list[str]
    non_editables: list[str]
    hiddens: list[str]
    mandatories: list[str]
    tooltips: dict[str, str]
    widths: dict[str, int]
    border_left_columns: list[str]
    page_size: int


CacheType = dict[str, _WBSTableCache]  # The response dict from '/table/config'


class TableConfigParser:  # pylint: disable=R0904
    """Manage caching and parsing responses from '/table/config'."""

    class _Constants:  # pylint: disable=R0903,R0902
        """Name-space for constants."""

        def __init__(self) -> None:
            # pylint: disable=C0103
            self.ID: Final[str] = "_id"
            self.WBS_L2: Final[str] = "WBS L2"
            self.WBS_L3: Final[str] = "WBS L3"
            self.LABOR_CAT: Final[str] = "Labor Cat."
            self.US_NON_US: Final[str] = "US / Non-US"
            self.INSTITUTION: Final[str] = "Institution"
            self.NAME: Final[str] = "Name"
            self.TASK_DESCRIPTION: Final[str] = "Task Description"
            self.SOURCE_OF_FUNDS_US_ONLY: Final[str] = "Source of Funds (U.S. Only)"
            self.FTE: Final[str] = "FTE"
            self.NSF_MO_CORE: Final[str] = "NSF M&O Core"
            self.NSF_BASE_GRANTS: Final[str] = "NSF Base Grants"
            self.US_IN_KIND: Final[str] = "US In-Kind"
            self.NON_US_IN_KIND: Final[str] = "Non-US In-Kind"
            self.GRAND_TOTAL: Final[str] = "Grand Total"
            self.TOTAL_COL: Final[str] = "Total-Row Description"
            self.TIMESTAMP: Final[str] = "Date & Time of Last Edit"
            self.EDITOR: Final[str] = "Name of Last Editor"

    def __init__(self, wbs_l1: str) -> None:
        """Get the dictionary of table configurations.

        Use the parser functions to access configurations.
        """
        self._wbs_l1 = wbs_l1
        self._configs: CacheType = self._cached_get_configs()

        # set up constants for quick reference
        self.const = TableConfigParser._Constants()

    @staticmethod
    @cachetools.func.ttl_cache(ttl=MAX_CACHE_MINS * 60)
    def _cached_get_configs() -> CacheType:
        logging.warning("Cache Miss: TableConfigParser._cached_get_configs()")
        return {
            k: _WBSTableCache(**v)
            for k, v in mou_request("GET", "/table/config").items()
        }

    def get_table_columns(self) -> list[str]:
        """Get table column's names."""
        cols = self._configs[self._wbs_l1].columns

        if self._wbs_l1 != "mo":
            cols = [
                c
                for c in cols
                if c
                not in [
                    self.const.SOURCE_OF_FUNDS_US_ONLY,
                    self.const.NSF_MO_CORE,
                    self.const.NSF_BASE_GRANTS,
                    self.const.US_IN_KIND,
                    self.const.NON_US_IN_KIND,
                ]
            ]

        return cols

    def get_column_tooltip(self, column: str) -> str:
        """Get the tooltip for the given column."""
        try:
            return self._configs[self._wbs_l1].tooltips[column]
        except KeyError:
            return column

    def get_simple_column_dropdown_menu(self, column: str) -> list[str]:
        """Get dropdown menu for a column."""
        return sorted(self._configs[self._wbs_l1].simple_dropdown_menus[column])

    def get_l2_categories(self) -> list[str]:
        """Get dropdown menu for a column."""
        return self.get_simple_column_dropdown_menu(self.const.WBS_L2)

    def get_labor_categories_w_abbrevs(self) -> list[tuple[str, str]]:
        """Get list of labors  and their abbreviations.."""
        return sorted(self._configs[self._wbs_l1].labor_categories, key=lambda k: k[1])

    def is_column_dropdown(self, column: str) -> bool:
        """Get whether column is a dropdown-type."""
        return column in self._configs[self._wbs_l1].dropdowns

    def is_column_numeric(self, column: str) -> bool:
        """Get whether column takes numeric data."""
        return column in self._configs[self._wbs_l1].numerics

    def is_column_editable(self, column: str) -> bool:
        """Get whether column data can be edited by end-user."""
        return column not in self._configs[self._wbs_l1].non_editables

    def get_non_editable_columns(self) -> list[str]:
        """Get the columns whose data cannot be edited by end-user."""
        return self._configs[self._wbs_l1].non_editables

    def get_hidden_columns(self) -> list[str]:
        """Get the columns hidden be default."""
        return self._configs[self._wbs_l1].hiddens

    def get_mandatory_columns(self) -> list[str]:
        """Get the columns that must be filled in by user."""
        return self._configs[self._wbs_l1].mandatories

    def get_always_hidden_columns(self) -> list[str]:
        """Get the columns that should never be shown to the user.

        AKA, columns that are marked as hidden and have width of `0`.
        """
        cols = [
            c
            for c in self._configs[self._wbs_l1].hiddens
            if not self.get_column_width(c)
        ]

        return cols

    def get_dropdown_columns(self) -> list[str]:
        """Get list of dropdown-type columns."""
        return self._configs[self._wbs_l1].dropdowns

    def is_simple_dropdown(self, column: str) -> bool:
        """Get whether column is a simple dropdown-type."""
        return column in self._configs[self._wbs_l1].simple_dropdown_menus.keys()

    def is_conditional_dropdown(self, column: str) -> bool:
        """Get whether column is a conditional dropdown-type."""
        return column in self._configs[self._wbs_l1].conditional_dropdown_menus.keys()

    def get_conditional_column_parent_and_options(
        self, column: str
    ) -> tuple[str, list[str]]:
        """Get the parent column's (name, list of options)."""
        return (
            self._configs[self._wbs_l1].conditional_dropdown_menus[column][0],
            list(
                self._configs[self._wbs_l1].conditional_dropdown_menus[column][1].keys()
            ),
        )

    def get_conditional_column_parent(self, column: str) -> str:
        """Get the parent column's name."""
        return self.get_conditional_column_parent_and_options(column)[0]

    def get_conditional_column_dropdown_menu(
        self, column: str, parent_col_option: str
    ) -> list[str]:
        """Get the dropdown menu for a conditional dropdown-column."""
        return self._configs[self._wbs_l1].conditional_dropdown_menus[column][1][
            parent_col_option
        ]

    def get_column_width(self, column: str, default: int = 35) -> int:
        """Get the pixel width of a given column."""
        try:
            return self._configs[self._wbs_l1].widths[column]
        except KeyError:
            return default

    def has_border_left(self, column: str) -> bool:
        """Get whether column has a border to its right."""
        return column in self._configs[self._wbs_l1].border_left_columns

    def get_page_size(self) -> int:
        """Get the number of rows for a page."""
        return self._configs[self._wbs_l1].page_size
