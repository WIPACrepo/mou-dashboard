"""Integration test web_app module."""


import sys

sys.path.append(".")
import web_app.data_source.table_config as tc  # isort:skip  # noqa # pylint: disable=E0401,C0413


class TestTableConfig:
    """Test data_source/table_config.py."""

    @staticmethod
    def test_const_w_columns() -> None:
        """Test that the constants agree with the rest server."""
        # mo
        tconfig = tc.TableConfigParser("mo")
        assert tconfig.const.__dict__.values()
        assert all(
            a in tconfig.get_table_columns() for a in tconfig.const.__dict__.values()
        )

        # upgrade
        tconfig = tc.TableConfigParser("upgrade")
        assert tconfig.const.__dict__.values()
        assert all(
            a in tconfig.get_table_columns()
            for a in tconfig.const.__dict__.values()
            if a
            not in [
                tconfig.const.SOURCE_OF_FUNDS_US_ONLY,
                tconfig.const.NSF_MO_CORE,
                tconfig.const.NSF_BASE_GRANTS,
                tconfig.const.US_IN_KIND,
                tconfig.const.NON_US_IN_KIND,
            ]
        )
