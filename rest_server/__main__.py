"""Root python script for MOU REST API server interface."""


import argparse
import asyncio
import dataclasses as dc
import json
import logging
from urllib.parse import quote_plus

import coloredlogs  # type: ignore[import]
from motor.motor_tornado import MotorClient
from rest_tools.server import RestHandlerSetup, RestServer

from .config import ENV
from .data_sources import mou_db, table_config_cache, todays_institutions
from .routes import (
    InstitutionStaticHandler,
    InstitutionValuesConfirmationHandler,
    InstitutionValuesConfirmationTouchstoneHandler,
    InstitutionValuesHandler,
    MainHandler,
    MakeSnapshotHandler,
    RecordHandler,
    SnapshotsHandler,
    TableConfigHandler,
    TableHandler,
)
from .utils import utils


async def start(debug: bool = False) -> RestServer:
    """Start a Mad Dash REST service."""
    for field in dc.fields(ENV):
        logging.info(
            f"{field.name}\t{getattr(ENV, field.name)}\t({type(getattr(ENV, field.name)).__name__})"
        )

    args = RestHandlerSetup(  # type: ignore[no-untyped-call]
        {
            "auth": {
                "openid_url": ENV.OPENID_URL,
                "audience": ENV.OPENID_AUDIENCE,
            },
            "debug": debug,
        }
    )

    # Setup Mongo
    mongodb_auth_user = quote_plus(ENV.MOU_MONGODB_AUTH_USER)
    mongodb_auth_pass = quote_plus(ENV.MOU_MONGODB_AUTH_PASS)
    mongodb_url = f"mongodb://{ENV.MOU_MONGODB_HOST}:{ENV.MOU_MONGODB_PORT}"
    if mongodb_auth_user and mongodb_auth_pass:
        mongodb_url = f"mongodb://{mongodb_auth_user}:{mongodb_auth_pass}@{ENV.MOU_MONGODB_HOST}:{ENV.MOU_MONGODB_PORT}"
    mou_db_client = mou_db.MOUDatabaseClient(
        MotorClient(mongodb_url),
        utils.MOUDataAdaptor(await table_config_cache.TableConfigCache.create()),
    )
    await mou_db_client._ensure_all_db_indexes()
    args["mou_db_client"] = mou_db_client

    # Configure REST Routes
    server = RestServer(debug=debug)
    server.add_route(MainHandler.ROUTE, MainHandler, args)  # get
    server.add_route(TableHandler.ROUTE, TableHandler, args)  # get, post
    server.add_route(SnapshotsHandler.ROUTE, SnapshotsHandler, args)  # get
    server.add_route(MakeSnapshotHandler.ROUTE, MakeSnapshotHandler, args)  # post
    server.add_route(RecordHandler.ROUTE, RecordHandler, args)  # post, delete
    server.add_route(TableConfigHandler.ROUTE, TableConfigHandler, args)  # get
    server.add_route(  # post, get
        InstitutionValuesConfirmationTouchstoneHandler.ROUTE,
        InstitutionValuesConfirmationTouchstoneHandler,
        args,
    )
    server.add_route(  # post
        InstitutionValuesConfirmationHandler.ROUTE,
        InstitutionValuesConfirmationHandler,
        args,
    )
    server.add_route(  # get, post
        InstitutionValuesHandler.ROUTE,
        InstitutionValuesHandler,
        args,
    )
    server.add_route(  # get
        InstitutionStaticHandler.ROUTE,
        InstitutionStaticHandler,
        args,
    )

    server.startup(address=ENV.MOU_REST_HOST, port=ENV.MOU_REST_PORT)
    return server


def main() -> None:
    """Configure logging and start a MOU data service."""
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

        async def _overridden_krs() -> list[todays_institutions.Institution]:
            return todays_institutions.convert_krs_institutions(json_insts)

        todays_institutions.request_krs_institutions = _overridden_krs

    main()
