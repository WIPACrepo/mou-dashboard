"""Root python script for MoU REST API server interface."""


import asyncio
import logging

# local imports
from rest_tools.server import (  # type: ignore
    from_environment,
    RestHandlerSetup,
    RestServer,
)

from .config import EXPECTED_CONFIG
from .routes import MainHandler


def start(debug: bool = False) -> RestServer:
    """Start a Mad Dash REST service."""
    config = from_environment(EXPECTED_CONFIG)

    for name in config:
        logging.info(f"{config[name]=}")

    args = RestHandlerSetup(
        {
            "auth": {
                "secret": config["MOU_AUTH_SECRET"],
                "issuer": config["MOU_AUTH_ISSUER"],
                "algorithm": config["MOU_AUTH_ALGORITHM"],
            },
            "debug": debug,
        }
    )

    # Configure Snapshot DB
    # TODO

    # Configure REST Routes
    server = RestServer(debug=debug)
    server.add_route(r"/$", MainHandler, args)
    # TODO

    return server


def main() -> None:
    """Configure logging and start a MoU data service."""
    logging.basicConfig(level=logging.DEBUG)
    start(debug=True)
    loop = asyncio.get_event_loop()
    loop.run_forever()


if __name__ == "__main__":
    main()
