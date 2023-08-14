"""Integration test web_app module."""

# pylint: disable=W0212,W0621


# import sys
# from typing import Iterator

# import pytest

# sys.path.append(".")
# import web_app.utils  # isort:skip  # noqa # pylint: disable=E0401,C0413
# from web_app.data_source import (  # isort:skip  # noqa # pylint: disable=E0401,C0413
#     table_config as tc,
#     connections,
# )


# @pytest.fixture(autouse=True)
# def clear_all_cachetools_func_caches() -> Iterator[None]:
#     """Clear all `cachetools.func` caches, everywhere."""
#     yield
#     connections._cached_get_institutions_infos.cache_clear()  # type: ignore[attr-defined]
#     tc.TableConfigParser._cached_get_configs.cache_clear()  # type: ignore[attr-defined]
#     web_app.data_source.connections.CurrentUser._cached_get_info.cache_clear()  # type: ignore[attr-defined]


# class TestTableConfig:
#     """Test data_source/table_config.py."""

#     @staticmethod
#     def test_const_w_columns() -> None:
#         """Test that the constants agree with the rest server."""
#         # mo
#         tconfig = tc.TableConfigParser("mo")
#         assert tconfig.const.__dict__.values()
#         assert all(
#             a in tconfig.get_table_columns() for a in tconfig.const.__dict__.values()
#         )

#         # upgrade
#         tconfig = tc.TableConfigParser("upgrade")
#         assert tconfig.const.__dict__.values()
#         assert all(
#             a in tconfig.get_table_columns()
#             for a in tconfig.const.__dict__.values()
#             if a
#             not in [
#                 tconfig.const.SOURCE_OF_FUNDS_US_ONLY,
#                 tconfig.const.NSF_MO_CORE,
#                 tconfig.const.NSF_BASE_GRANTS,
#                 tconfig.const.US_IN_KIND,
#                 tconfig.const.NON_US_IN_KIND,
#             ]
#         )
