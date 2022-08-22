"""Root python script for MoU REST API server interface."""


import argparse
import asyncio
import dataclasses as dc
import json
import logging
from typing import List
from urllib.parse import quote_plus

import coloredlogs  # type: ignore[import]
from rest_tools.server import RestHandlerSetup, RestServer
from wipac_dev_tools import from_environment_as_dataclass

from . import config
from .data_sources import table_config_cache, todays_institutions
from .routes import (
    InstitutionStaticHandler,
    InstitutionValuesHandler,
    MainHandler,
    MakeSnapshotHandler,
    RecordHandler,
    SnapshotsHandler,
    TableConfigHandler,
    TableHandler,
)


async def start(debug: bool = False) -> RestServer:
    """Start a Mad Dash REST service."""
    env = from_environment_as_dataclass(config.EnvConfig)
    for field in dc.fields(env):
        logging.info(
            f"{field.name}\t{getattr(env, field.name)}\t({type(getattr(env, field.name)).__name__})"
        )

    args = RestHandlerSetup(  # type: ignore[no-untyped-call]
        {
            "auth": {
                "secret": env.MOU_AUTH_SECRET,
                "issuer": env.MOU_AUTH_ISSUER,
                "algorithm": env.MOU_AUTH_ALGORITHM,
            },
            "debug": debug,
        }
    )
    args["tc_cache"] = await table_config_cache.TableConfigCache.create()

    # Setup DB URL
    mongodb_auth_user = quote_plus(env.MOU_MONGODB_AUTH_USER)
    mongodb_auth_pass = quote_plus(env.MOU_MONGODB_AUTH_PASS)
    mongodb_url = f"mongodb://{env.MOU_MONGODB_HOST}:{env.MOU_MONGODB_PORT}"
    if mongodb_auth_user and mongodb_auth_pass:
        mongodb_url = f"mongodb://{mongodb_auth_user}:{mongodb_auth_pass}@{env.MOU_MONGODB_HOST}:{env.MOU_MONGODB_PORT}"
    args["mongodb_url"] = mongodb_url

    # Configure REST Routes
    server = RestServer(debug=debug)
    server.add_route(MainHandler.ROUTE, MainHandler, args)  # get
    server.add_route(TableHandler.ROUTE, TableHandler, args)  # get, post
    server.add_route(SnapshotsHandler.ROUTE, SnapshotsHandler, args)  # get
    server.add_route(MakeSnapshotHandler.ROUTE, MakeSnapshotHandler, args)  # post
    server.add_route(RecordHandler.ROUTE, RecordHandler, args)  # post, delete
    server.add_route(TableConfigHandler.ROUTE, TableConfigHandler, args)  # get
    server.add_route(  # get, post
        InstitutionValuesHandler.ROUTE, InstitutionValuesHandler, args
    )
    server.add_route(  # get
        InstitutionStaticHandler.ROUTE, InstitutionStaticHandler, args
    )

    server.startup(address=env.MOU_REST_HOST, port=env.MOU_REST_PORT)
    return server


def main() -> None:
    """Configure logging and start a MoU data service."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start(debug=True))
    loop.run_forever()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log", default="DEBUG", help="the output logging level")
    parser.add_argument(
        "--override-krs-insts",
        default=None,
        help="Don't actually connect to krs. Read from this json file instead. "
        "This is meant for testing only.",
    )
    _args = parser.parse_args()

    coloredlogs.install(level=getattr(logging, _args.log.upper()))

    if _args.override_krs_insts:
        logging.warning(
            f"Using Overriding KRS Institution Data: {_args.override_krs_insts}"
        )
        with open(_args.override_krs_insts) as f:
            json_insts = json.load(f)

        async def _overridden_krs() -> List[todays_institutions.Institution]:
            return todays_institutions.convert_krs_institutions(json_insts)

        todays_institutions.request_krs_institutions = _overridden_krs

    main()
