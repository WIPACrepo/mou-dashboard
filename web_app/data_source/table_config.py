"""REST interface for get configurations for the table/columns."""


from typing import cast, Dict, List, Optional, Tuple, TypedDict

from .utils import mou_request

_WBS_L2 = "WBS L2"


class _WBSTableCache(TypedDict):  # pylint: disable=R0903
    """The response dict from '/table/config'."""

    columns: List[str]
    simple_dropdown_menus: Dict[str, List[str]]
    institutions: List[Tuple[str, str]]
    labor_categories: List[str]
    conditional_dropdown_menus: Dict[str, Tuple[str, Dict[str, List[str]]]]
    dropdowns: List[str]
    numerics: List[str]
    non_editables: List[str]
    hiddens: List[str]
    tooltips: Dict[str, str]
    widths: Dict[str, int]
    border_left_columns: List[str]
    page_size: int


class TableConfigParser:  # pylint: disable=R0904
    """Manage caching and parsing responses from '/table/config'."""

    CacheType = Dict[str, _WBSTableCache]  # The response dict from '/table/config'

    def __init__(self, cached_tconfigs: Optional[CacheType] = None) -> None:
        """Get the dictionary of table configurations.

        Use the parser functions to access configurations.
        """
        if cached_tconfigs:
            self._configs = cached_tconfigs
        else:
            self._configs = cast(
                TableConfigParser.CacheType, mou_request("GET", "/table/config")
            )

    def get_configs(self) -> CacheType:
        """Get the `_configs` dict for caching."""
        return self._configs

    def get_table_columns(self, wbs_l1: str) -> List[str]:
        """Get table column's names."""
        return self._configs[wbs_l1]["columns"]

    def get_column_tooltip(self, wbs_l1: str, column: str) -> str:
        """Get the tooltip for the given column."""
        try:
            return self._configs[wbs_l1]["tooltips"][column]
        except KeyError:
            return column

    def get_simple_column_dropdown_menu(self, wbs_l1: str, column: str) -> List[str]:
        """Get dropdown menu for a column."""
        return sorted(self._configs[wbs_l1]["simple_dropdown_menus"][column])

    def get_l2_categories(self, wbs_l1: str) -> List[str]:
        """Get dropdown menu for a column."""
        return self.get_simple_column_dropdown_menu(wbs_l1, _WBS_L2)

    def get_institutions_w_abbrevs(self, wbs_l1: str) -> List[Tuple[str, str]]:
        """Get list of institutions and their abbreviations."""
        return sorted(self._configs[wbs_l1]["institutions"], key=lambda k: k[1])

    def get_labor_categories(self, wbs_l1: str) -> List[str]:
        """Get list of labors."""
        return sorted(self._configs[wbs_l1]["labor_categories"])

    def is_column_dropdown(self, wbs_l1: str, column: str) -> bool:
        """Get whether column is a dropdown-type."""
        return column in self._configs[wbs_l1]["dropdowns"]

    def is_column_numeric(self, wbs_l1: str, column: str) -> bool:
        """Get whether column takes numeric data."""
        return column in self._configs[wbs_l1]["numerics"]

    def is_column_editable(self, wbs_l1: str, column: str) -> bool:
        """Get whether column data can be edited by end-user."""
        return column not in self._configs[wbs_l1]["non_editables"]

    def get_non_editable_columns(self, wbs_l1: str) -> List[str]:
        """Get the columns whose data cannot be edited by end-user."""
        return self._configs[wbs_l1]["non_editables"]

    def get_hidden_columns(self, wbs_l1: str) -> List[str]:
        """Get the columns hidden be default."""
        return self._configs[wbs_l1]["hiddens"]

    def get_always_hidden_columns(self, wbs_l1: str) -> List[str]:
        """Get the columns that should never be shown to the user.

        AKA, columns that are marked as hidden and have width of `0`.
        """
        return [
            c
            for c in self._configs[wbs_l1]["hiddens"]
            if not self.get_column_width(wbs_l1, c)
        ]

    def get_dropdown_columns(self, wbs_l1: str) -> List[str]:
        """Get list of dropdown-type columns."""
        return self._configs[wbs_l1]["dropdowns"]

    def is_simple_dropdown(self, wbs_l1: str, column: str) -> bool:
        """Get whether column is a simple dropdown-type."""
        return column in self._configs[wbs_l1]["simple_dropdown_menus"].keys()

    def is_conditional_dropdown(self, wbs_l1: str, column: str) -> bool:
        """Get whether column is a conditional dropdown-type."""
        return column in self._configs[wbs_l1]["conditional_dropdown_menus"].keys()

    def get_conditional_column_parent_and_options(
        self, wbs_l1: str, column: str
    ) -> Tuple[str, List[str]]:
        """Get the parent column's (name, list of options)."""
        return (
            self._configs[wbs_l1]["conditional_dropdown_menus"][column][0],
            list(self._configs[wbs_l1]["conditional_dropdown_menus"][column][1].keys()),
        )

    def get_conditional_column_parent(self, wbs_l1: str, column: str) -> str:
        """Get the parent column's name."""
        return self.get_conditional_column_parent_and_options(wbs_l1, column)[0]

    def get_conditional_column_dropdown_menu(
        self, wbs_l1: str, column: str, parent_col_option: str
    ) -> List[str]:
        """Get the dropdown menu for a conditional dropdown-column."""
        return self._configs[wbs_l1]["conditional_dropdown_menus"][column][1][
            parent_col_option
        ]

    def get_column_width(self, wbs_l1: str, column: str, default: int = 35) -> int:
        """Get the pixel width of a given column."""
        try:
            return self._configs[wbs_l1]["widths"][column]
        except KeyError:
            return default

    def has_border_left(self, wbs_l1: str, column: str) -> bool:
        """Get whether column has a border to its right."""
        return column in self._configs[wbs_l1]["border_left_columns"]

    def get_page_size(self, wbs_l1: str) -> int:
        """Get the number of rows for a page."""
        return self._configs[wbs_l1]["page_size"]
