"""Root python script for MoU REST API server interface."""


import argparse
import asyncio
import logging
from urllib.parse import quote_plus

import coloredlogs  # type: ignore[import]
from motor.motor_tornado import MotorClient  # type: ignore

# local imports
from rest_tools.server import RestHandlerSetup, RestServer  # type: ignore
from rest_tools.server.config import from_environment  # type: ignore[import]

from . import config, routes
from .utils import db_utils


def start(debug: bool = False, xlsx: str = "") -> RestServer:
    """Start a Mad Dash REST service."""
    config_env = from_environment(config.DEFAULT_ENV_CONFIG)
    config.log_environment(config_env)

    mongodb_auth_user = quote_plus(config_env["MOU_MONGODB_AUTH_USER"])
    mongodb_auth_pass = quote_plus(config_env["MOU_MONGODB_AUTH_PASS"])
    mongodb_host = config_env["MOU_MONGODB_HOST"]
    mongodb_port = int(config_env["MOU_MONGODB_PORT"])

    args = RestHandlerSetup(
        {
            "auth": {
                "secret": config_env["MOU_AUTH_SECRET"],
                "issuer": config_env["MOU_AUTH_ISSUER"],
                "algorithm": config_env["MOU_AUTH_ALGORITHM"],
            },
            "debug": debug,
        }
    )

    # Setup DB
    mongodb_url = f"mongodb://{mongodb_host}:{mongodb_port}"
    if mongodb_auth_user and mongodb_auth_pass:
        mongodb_url = f"mongodb://{mongodb_auth_user}:{mongodb_auth_pass}@{mongodb_host}:{mongodb_port}"
    args["db_client"] = db_utils.MoUMotorClient(MotorClient(mongodb_url), xlsx=xlsx)

    # Configure REST Routes
    server = RestServer(debug=debug)
    server.add_route(r"/$", routes.MainHandler, args)
    server.add_route(r"/table/data$", routes.TableHandler, args)  # get
    server.add_route(r"/snapshots/timestamps$", routes.SnapshotsHandler, args)  # get
    server.add_route(r"/snapshots/make$", routes.MakeSnapshotHandler, args)  # post
    server.add_route(r"/record$", routes.RecordHandler, args)  # push, delete
    server.add_route(r"/table/config$", routes.TableConfigHandler, args)  # get

    server.startup(
        address=config_env["MOU_REST_HOST"], port=int(config_env["MOU_REST_PORT"])
    )
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
    _args = parser.parse_args()

    coloredlogs.install(level=getattr(logging, _args.log.upper()))
    main(_args.xlsx)
