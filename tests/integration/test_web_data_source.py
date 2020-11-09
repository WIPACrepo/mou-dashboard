"""Integration test web_app module."""


import sys

sys.path.append(".")
import web_app.data_source.table_config as tc  # isort:skip  # noqa # pylint: disable=E0401,C0413


class TestTableConfig:
    """Test data_source/table_config.py."""

    @staticmethod
    def test_const_w_columns() -> None:
        """Test that the constants agree with the rest server."""
        for wbs in ["mo", "upgrade"]:
            tconfig = tc.TableConfigParser(wbs)
            assert tconfig.const.__dict__.values()
            assert all(
                a in tconfig.get_table_columns()
                for a in tconfig.const.__dict__.values()
            )
