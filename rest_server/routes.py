"""Routes handlers for the MoU REST API server interface."""


from typing import Any

# local imports
from rest_tools.server import RestHandler  # type: ignore

from .config import AUTH_PREFIX

# -----------------------------------------------------------------------------


class BaseMoUHandler(RestHandler):  # type: ignore  # pylint: disable=W0223
    """BaseMoUHandler is a RestHandler for all MoU routes."""

    def initialize(  # pylint: disable=W0221
        self, motor_client: MotorClient, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize a BaseMoUHandler object."""
        super().initialize(*args, **kwargs)
        # self.motor_client = motor_client  # pylint: disable=W0201
        # self.md_mc = MoUMotorClient(motor_client)  # pylint: disable=W0201


# -----------------------------------------------------------------------------


class MainHandler(BaseMoUHandler):  # pylint: disable=W0223
    """MainHandler is a BaseMoUHandler that handles the root route."""

    def get(self) -> None:
        """Handle GET."""
        self.write({})
