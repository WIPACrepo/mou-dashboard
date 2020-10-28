"""REST interface for get configurations for the table/columns."""


from typing import cast, Dict, List, Optional, Tuple, TypedDict

from .utils import mou_request


class TableConfigParser:
    """Manage caching and parsing responses from '/table/config'."""

    class Cache(TypedDict):  # pylint: disable=R0903
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

    def __init__(self, cached_table_config: Optional[Cache] = None) -> None:
        """Return the dictionary of table configurations.

        Use the parser functions to access configurations.
        """
        if cached_table_config:
            self.config = cached_table_config
        else:
            self.config = cast(
                TableConfigParser.Cache, mou_request("GET", "/table/config")
            )

    def get_table_columns(self) -> List[str]:
        """Return table column's names."""
        return self.config["columns"]

    def get_column_tooltip(self, column: str) -> str:
        """Return the tooltip for the given column."""
        try:
            return self.config["tooltips"][column]
        except KeyError:
            return column

    def get_simple_column_dropdown_menu(self, column: str) -> List[str]:
        """Return dropdown menu for a column."""
        return sorted(self.config["simple_dropdown_menus"][column])

    def get_institutions_w_abbrevs(self) -> List[Tuple[str, str]]:
        """Return list of institutions and their abbreviations."""
        return sorted(self.config["institutions"], key=lambda k: k[1])

    def get_labor_categories(self) -> List[str]:
        """Return list of labors."""
        return sorted(self.config["labor_categories"])

    def is_column_dropdown(self, column: str) -> bool:
        """Return  whether column is a dropdown-type."""
        return column in self.config["dropdowns"]

    def is_column_numeric(self, column: str) -> bool:
        """Return whether column takes numeric data."""
        return column in self.config["numerics"]

    def is_column_editable(self, column: str) -> bool:
        """Return whether column data can be edited by end-user."""
        return column not in self.config["non_editables"]

    def get_non_editable_columns(self) -> List[str]:
        """The columns whose data cannot be edited by end-user."""
        return self.config["non_editables"]

    def get_hidden_columns(self) -> List[str]:
        """Return the columns hidden be default."""
        return self.config["hiddens"]

    def get_always_hidden_columns(self) -> List[str]:
        """Return the columns that should never be shown to the user.

        AKA, columns that are marked as hidden and have width of `0`.
        """
        return [c for c in self.config["hiddens"] if not self.get_column_width(c)]

    def get_dropdown_columns(self) -> List[str]:
        """Return list of dropdown-type columns."""
        return self.config["dropdowns"]

    def is_simple_dropdown(self, column: str) -> bool:
        """Return whether column is a simple dropdown-type."""
        return column in self.config["simple_dropdown_menus"].keys()

    def is_conditional_dropdown(self, column: str) -> bool:
        """Return whether column is a conditional dropdown-type."""
        return column in self.config["conditional_dropdown_menus"].keys()

    def get_conditional_column_parent_and_options(
        self, column: str
    ) -> Tuple[str, List[str]]:
        """Get the parent column's (name, list of options)."""
        return (
            self.config["conditional_dropdown_menus"][column][0],
            list(self.config["conditional_dropdown_menus"][column][1].keys()),
        )

    def get_conditional_column_parent(self, column: str) -> str:
        """Get the parent column's name."""
        return self.get_conditional_column_parent_and_options(column)[0]

    def get_conditional_column_dropdown_menu(
        self, column: str, parent_col_option: str
    ) -> List[str]:
        """Get the dropdown menu for a conditional dropdown-column."""
        return self.config["conditional_dropdown_menus"][column][1][parent_col_option]

    def get_column_width(self, column: str, default: int = 35) -> int:
        """Return the pixel width of a given column."""
        try:
            return self.config["widths"][column]
        except KeyError:
            return default

    def has_border_left(self, column: str) -> bool:
        """Return whether column has a border to its right."""
        return column in self.config["border_left_columns"]

    def get_page_size(self) -> int:
        """Return the number of rows for a page."""
        return self.config["page_size"]
