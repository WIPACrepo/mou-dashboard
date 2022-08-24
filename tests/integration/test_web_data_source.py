"""Integration test web_app module."""

# pylint: disable=W0212,W0621


from typing import Iterator

import pytest
import web_app.utils
from web_app.data_source import institution_info
from web_app.data_source import table_config as tc


@pytest.fixture(autouse=True)
def clear_all_cachetools_func_caches() -> Iterator[None]:
    """Clear all `cachetools.func` caches, everywhere"""
    yield
    institution_info._cached_get_institutions_infos.cache_clear()  # type: ignore[attr-defined]
    tc.TableConfigParser._cached_get_configs.cache_clear()  # type: ignore[attr-defined]
    web_app.utils.oidc_tools.CurrentUser._cached_get_info.cache_clear()  # type: ignore[attr-defined]


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
