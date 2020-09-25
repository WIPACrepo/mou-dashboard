"""Unit test web_app module."""

# pylint: disable=W0212


import inspect
import sys
from copy import deepcopy
from typing import Any, Final

import pytest
import requests

sys.path.append(".")
from web_app.utils import (  # isort:skip  # noqa # pylint: disable=E0401,C0413
    dash_utils,
    data_source,
    types,
)


class TestDashUtils:
    """Test dash_utils.py."""

    RECORD: Final[types.Record] = {"a": "AA", "b": "BB", "c": "CC"}

    def _get_new_record(self) -> types.Record:
        return deepcopy(self.RECORD)

    def test_add_original_copies_to_record(self) -> None:
        """Test add_original_copies_to_record()."""
        record = self._get_new_record()
        record_orig = deepcopy(record)

        for _ in range(2):
            record_out = dash_utils.add_original_copies_to_record(record)
            assert record_out == record  # check in-place update
            assert len(record) == 2 * len(record_orig)
            # check copied values
            for key in record_orig.keys():
                assert record_orig[key] == record[key]
                assert record_orig[key] == record[key + dash_utils._OC_SUFFIX]

    def test_add_original_copies_to_record_novel(self) -> None:
        """Test add_original_copies_to_record(novel=True)."""
        record = self._get_new_record()
        record_orig = deepcopy(record)

        for _ in range(2):
            record_out = dash_utils.add_original_copies_to_record(record, novel=True)
            assert record_out == record  # check in-place update
            assert len(record) == 2 * len(record_orig)
            # check copied values
            for key in record_orig.keys():
                assert record_orig[key] == record[key]
                # check only keys were copied with _OC_SUFFIX, not values
                assert record_orig[key] != record[key + dash_utils._OC_SUFFIX]
                assert record[key + dash_utils._OC_SUFFIX] == ""

    def test_without_original_copies_from_record(self) -> None:
        """Test without_original_copies_from_record()."""
        record = self._get_new_record()
        record_orig = deepcopy(record)

        dash_utils.add_original_copies_to_record(record)
        record_out = dash_utils.without_original_copies_from_record(record)

        assert record_out != record
        assert record_out == record_orig


class TestDataSource:
    """Test data_source.py."""

    REST_PATCH: Final[str] = "web_app.utils.data_source._ds_rest_connection"

    @pytest.fixture  # type: ignore
    def mock_rest(self, mocker: Any) -> Any:
        """Patch mock_rest."""
        return mocker.patch(self.REST_PATCH)

    @staticmethod
    def test_pull_data_table(mock_rest: Any) -> None:
        """Test pull_data_table()."""
        response = {"foo": 0, "table": [{"a": "a"}, {"b": 2}, {"c": None}]}
        bodies = [
            {  # Default values
                "institution": "",
                "labor": "",
                "total_rows": False,
                "snapshot": "",
                "restore_id": "",
            },
            {  # Other values
                "institution": "bar",
                "labor": "baz",
                "total_rows": True,
                "snapshot": "123",
                "restore_id": "456789456123",
            },
        ]

        for i, _ in enumerate(bodies):
            # Call
            mock_rest.return_value.request_seq.return_value = response
            # Default values
            if i == 0:
                ret = data_source.pull_data_table()
            # Other values
            else:
                ret = data_source.pull_data_table(
                    bodies[i]["institution"],  # type: ignore[arg-type]
                    bodies[i]["labor"],  # type: ignore[arg-type]
                    bodies[i]["total_rows"],  # type: ignore[arg-type]
                    bodies[i]["snapshot"],  # type: ignore[arg-type]
                    bodies[i]["restore_id"],  # type: ignore[arg-type]
                )

            # Assert
            mock_rest.return_value.request_seq.assert_called_with(
                "GET", "/table/data", bodies[i]
            )
            assert ret == response["table"]

    @staticmethod
    def test_push_record(mock_rest: Any) -> None:
        """Test push_record()."""
        response = {"foo": 0, "record": {"x": "foo", "y": 22, "z": "z"}}
        bodies = [
            # Default values
            {"institution": "", "labor": "", "record": {"BAR": 23}},
            # Other values
            {"institution": "foo", "labor": "bar", "record": {"a": 1}},
        ]

        for i, _ in enumerate(bodies):
            # Call
            mock_rest.return_value.request_seq.return_value = response
            # Default values
            if i == 0:
                ret = data_source.push_record(bodies[0]["record"])  # type: ignore[arg-type]
            # Other values
            else:
                ret = data_source.push_record(
                    bodies[i]["record"], bodies[i]["labor"], bodies[i]["institution"]  # type: ignore[arg-type]
                )

            # Assert
            mock_rest.return_value.request_seq.assert_called_with(
                "POST", "/record", bodies[i]
            )
            assert ret == response["record"]

    @staticmethod
    def test_delete_record(mock_rest: Any) -> None:
        """Test delete_record()."""
        record = {"BAR": 23}

        # Call
        ret = data_source.delete_record(record)  # type: ignore[arg-type]

        # Assert
        mock_rest.return_value.request_seq.assert_called_with(
            "DELETE", "/record", {"record": record}
        )
        assert ret

        # Fail Test #
        # Call
        mock_rest.return_value.request_seq.side_effect = requests.exceptions.HTTPError
        ret = data_source.delete_record(record)  # type: ignore[arg-type]

        # Assert
        mock_rest.return_value.request_seq.assert_called_with(
            "DELETE", "/record", {"record": record}
        )
        assert not ret

    @staticmethod
    def test_list_snapshot_timestamps(mock_rest: Any) -> None:
        """Test list_snapshot_timestamps()."""
        response = {"timestamps": ["a", "b", "c"], "foo": "bar"}

        # Call
        mock_rest.return_value.request_seq.return_value = response
        ret = data_source.list_snapshot_timestamps()

        # Assert
        mock_rest.return_value.request_seq.assert_called_with(
            "GET", "/snapshots/timestamps", None
        )
        assert ret == response["timestamps"]

    @staticmethod
    def test_create_snapshot(mock_rest: Any) -> None:
        """Test create_snapshot()."""
        response = {"timestamp": "a", "foo": "bar"}

        # Call
        mock_rest.return_value.request_seq.return_value = response
        ret = data_source.create_snapshot()

        # Assert
        mock_rest.return_value.request_seq.assert_called_with(
            "POST", "/snapshots/make", None
        )
        assert ret == response["timestamp"]

    @staticmethod
    def test_table_config(mock_rest: Any) -> None:
        """Test TableConfig()."""
        # nonsense data, but correctly typed
        response: data_source.TableConfig._ResponseTypedDict = {
            "columns": ["a", "b", "c", "d"],
            "simple_dropdown_menus": {"a": ["1", "2", "3"], "c": ["4", "44", "444"]},
            "institutions": ["foo", "bar"],
            "labor_categories": ["foobar", "baz"],
            "conditional_dropdown_menus": {
                "column1": (
                    "parent_of_1",
                    {"optA": ["alpha", "a", "atlantic"], "optB": ["beta", "b", "boat"]},
                ),
                "column2": (
                    "parent_of_2",
                    {"optD": ["delta", "d", "dock"], "optG": ["gamma", "g", "gulf"]},
                ),
            },
            "dropdowns": ["gamma", "mu"],
            "numerics": ["foobarbaz"],
            "non_editables": ["alpha", "beta"],
            "hiddens": ["z", "y", "x"],
            "widths": {"Zetta": 888, "Yotta": -50},
            "border_left_columns": ["ee", "e"],
            "page_size": 55,
        }

        # Call
        mock_rest.return_value.request_seq.return_value = response
        table_config = data_source.TableConfig()

        # Assert
        mock_rest.return_value.request_seq.assert_called_with(
            "GET", "/table/config", None
        )
        assert table_config.config == response

        # no-argument methods
        assert table_config.get_table_columns() == response["columns"]
        assert table_config.get_institutions() == response["institutions"]
        assert table_config.get_labor_categories() == response["labor_categories"]
        assert table_config.get_hidden_columns() == response["hiddens"]
        assert table_config.get_dropdown_columns() == response["dropdowns"]
        assert table_config.get_page_size() == response["page_size"]

        # is_column_*()
        for col in response["dropdowns"]:
            assert table_config.is_column_dropdown(col)
            assert not table_config.is_column_dropdown(col + "!")
        for col in response["numerics"]:
            assert table_config.is_column_numeric(col)
            assert not table_config.is_column_numeric(col + "!")
        for col in response["non_editables"]:
            assert not table_config.is_column_editable(col)
            assert table_config.is_column_editable(col + "!")
        for col in response["simple_dropdown_menus"]:
            assert table_config.is_simple_dropdown(col)
            assert not table_config.is_simple_dropdown(col + "!")
        for col in response["conditional_dropdown_menus"]:
            assert table_config.is_conditional_dropdown(col)
            assert not table_config.is_conditional_dropdown(col + "!")
        for col in response["border_left_columns"]:
            assert table_config.has_border_left(col)
            assert not table_config.has_border_left(col + "!")

        # get_simple_column_dropdown_menu()
        for col, menu in response["simple_dropdown_menus"].items():
            assert table_config.get_simple_column_dropdown_menu(col) == menu
            with pytest.raises(KeyError):
                table_config.get_simple_column_dropdown_menu(col + "!")

        # get_conditional_column_parent()
        for col, par_opts in response["conditional_dropdown_menus"].items():
            assert table_config.get_conditional_column_parent(col) == (
                par_opts[0],  # parent
                list(par_opts[1].keys()),  # options
            )
            with pytest.raises(KeyError):
                table_config.get_conditional_column_parent(col + "!")

        # get_conditional_column_dropdown_menu()
        for col, par_opts in response["conditional_dropdown_menus"].items():
            for parent_col_option, menu in par_opts[1].items():
                assert (
                    table_config.get_conditional_column_dropdown_menu(
                        col, parent_col_option
                    )
                    == menu
                )
                with pytest.raises(KeyError):
                    table_config.get_conditional_column_dropdown_menu(
                        col + "!", parent_col_option
                    )
                    table_config.get_conditional_column_dropdown_menu(
                        col, parent_col_option + "!"
                    )

        # Error handling methods
        for col, wid in response["widths"].items():
            assert table_config.get_column_width(col) == wid
        mock_rest.return_value.request_seq.return_value = {}
        table_config = data_source.TableConfig()
        for col, wid in response["widths"].items():
            default = (
                inspect.signature(table_config.get_column_width)
                .parameters["default"]
                .default
            )
            assert table_config.get_column_width(col) == default

    @staticmethod
    def test_id_constant() -> None:
        """Check the ID constant, this corresponds to the mongodb id field."""
        assert data_source.ID == "_id"
