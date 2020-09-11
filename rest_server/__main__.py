"""Root python script for MoU REST API server interface."""


import asyncio
import logging

# local imports
from rest_tools.server import RestHandlerSetup, RestServer  # type: ignore

from . import routes
from .config import (
    log_environment,
    MOU_AUTH_ALGORITHM,
    MOU_AUTH_ISSUER,
    MOU_AUTH_SECRET,
    MOU_REST_HOST,
    MOU_REST_PORT,
)


def start(debug: bool = False) -> RestServer:
    """Start a Mad Dash REST service."""
    log_environment()

    args = RestHandlerSetup(
        {
            "auth": {
                "secret": MOU_AUTH_SECRET,
                "issuer": MOU_AUTH_ISSUER,
                "algorithm": MOU_AUTH_ALGORITHM,
            },
            "debug": debug,
        }
    )

    # Configure Snapshot DB
    # TODO

    # Configure REST Routes
    server = RestServer(debug=debug)

    # server.add_route(r"/table/data$", TableHandler, args)  # get

    # server.add_route(r"/table/data/snapshot$", SnapshotHandler, args)  # get, push

    # server.add_route(r"/record$", RecordHandler, args)  # push, delete

    server.add_route(r"/table/config$", routes.TableConfigHandler, args)  # get

    server.startup(address=MOU_REST_HOST, port=MOU_REST_PORT)
    return server


def main() -> None:
    """Configure logging and start a MoU data service."""
    logging.basicConfig(level=logging.DEBUG)
    start(debug=True)
    loop = asyncio.get_event_loop()
    loop.run_forever()


if __name__ == "__main__":
    main()
