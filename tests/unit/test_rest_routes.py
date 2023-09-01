"""Unit test rest_server module."""


# pylint: disable=W0212,W0621


from rest_server import routes


class TestNoArgumentRoutes:
    """Test routes.py routes that don't require arguments."""

    @staticmethod
    def test_main_get() -> None:
        """Test `GET` @ `/`."""
        assert routes.MainHandler.ROUTE == r"/$"
        assert "get" in dir(routes.MainHandler)

    @staticmethod
    def test_snapshots_timestamps_get() -> None:
        """Test `GET` @ `/snapshots/list`."""
        assert (
            routes.SnapshotsHandler.ROUTE
            == rf"/snapshots/list/(?P<wbs_l1>{routes._WBS_L1_REGEX_VALUES})$"
        )
        assert "get" in dir(routes.SnapshotsHandler)

    @staticmethod
    def test_snapshots_make_post() -> None:
        """Test `POST` @ `/snapshots/make`."""
        assert (
            routes.MakeSnapshotHandler.ROUTE
            == rf"/snapshots/make/(?P<wbs_l1>{routes._WBS_L1_REGEX_VALUES})$"
        )
        assert "post" in dir(routes.MakeSnapshotHandler)

        # NOTE: reserve testing POST for test_snapshots()

    @staticmethod
    def test_table_config_get() -> None:
        """Test `GET` @ `/table/config`."""
        assert routes.TableConfigHandler.ROUTE == r"/table/config$"
        assert "get" in dir(routes.TableConfigHandler)

    @staticmethod
    def test_institution_static_get() -> None:
        """Test `GET` @ `/institution/today`."""
        assert routes.InstitutionStaticHandler.ROUTE == r"/institution/today$"
        assert "get" in dir(routes.InstitutionStaticHandler)


class TestTableHandler:
    """Test `/table/data`."""

    @staticmethod
    def test_sanity() -> None:
        """Check routes and methods are there."""
        assert (
            routes.TableHandler.ROUTE
            == rf"/table/data/(?P<wbs_l1>{routes._WBS_L1_REGEX_VALUES})$"
        )
        assert "get" in dir(routes.TableHandler)


class TestRecordHandler:
    """Test `/record`."""

    @staticmethod
    def test_sanity() -> None:
        """Check routes and methods are there."""
        assert (
            routes.RecordHandler.ROUTE
            == rf"/record/(?P<wbs_l1>{routes._WBS_L1_REGEX_VALUES})$"
        )
        assert "post" in dir(routes.RecordHandler)
        assert "delete" in dir(routes.RecordHandler)


class TestInstitutionValuesHandler:
    """Test `/institution/values/*`."""

    @staticmethod
    def test_sanity() -> None:
        """Check routes and methods are there."""
        assert (
            routes.InstitutionValuesHandler.ROUTE
            == rf"/institution/values/(?P<wbs_l1>{routes._WBS_L1_REGEX_VALUES})$"
        )
        assert "post" in dir(routes.InstitutionValuesHandler)
        assert "get" in dir(routes.InstitutionValuesHandler)
