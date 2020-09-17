"""Root python script for MoU REST API server interface."""


import argparse
import asyncio
import logging

from motor.motor_tornado import MotorClient  # type: ignore

# local imports
from rest_tools.server import RestHandlerSetup, RestServer  # type: ignore

from . import routes
from .config import (
    AUTH_ALGORITHM,
    AUTH_ISSUER,
    AUTH_SECRET,
    log_environment,
    MONGODB_AUTH_PASS,
    MONGODB_AUTH_USER,
    MONGODB_HOST,
    MONGODB_PORT,
    REST_HOST,
    REST_PORT,
)
from .utils import db_utils


def start(debug: bool = False, xlsx: str = "") -> RestServer:
    """Start a Mad Dash REST service."""
    log_environment()

    args = RestHandlerSetup(
        {
            "auth": {
                "secret": AUTH_SECRET,
                "issuer": AUTH_ISSUER,
                "algorithm": AUTH_ALGORITHM,
            },
            "debug": debug,
        }
    )

    # Setup DB
    mongodb_url = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}"
    if MONGODB_AUTH_USER and MONGODB_AUTH_PASS:
        mongodb_url = f"mongodb://{MONGODB_AUTH_USER}:{MONGODB_AUTH_PASS}@{MONGODB_HOST}:{MONGODB_PORT}"
    args["db_client"] = db_utils.MoUMotorClient(MotorClient(mongodb_url), xlsx=xlsx)

    # Configure REST Routes
    server = RestServer(debug=debug)
    server.add_route(r"/$", routes.MainHandler, args)
    server.add_route(r"/table/data$", routes.TableHandler, args)  # get
    # server.add_route(r"/table/data/snapshot$", SnapshotHandler, args)  # get, push
    server.add_route(r"/record$", routes.RecordHandler, args)  # push, delete
    server.add_route(r"/table/config$", routes.TableConfigHandler, args)  # get

    server.startup(address=REST_HOST, port=REST_PORT)
    return server


def main(xlsx: str) -> None:
    """Configure logging and start a MoU data service."""
    start(debug=True, xlsx=xlsx)
    loop = asyncio.get_event_loop()
    loop.run_forever()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-x", "--xlsx", help=".xlsx file to ingest as a collection.")
    parser.add_argument("-l", "--log", default="DEBUG", help="the output logging level")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log.upper()))
    main(args.xlsx)
