"""Root python script for MOU Dashboard web application."""

import argparse
import logging

import coloredlogs  # type: ignore[import]

from web_app.config import ENV, app, log_config_vars

from . import layout


def main() -> None:
    """Start up application context."""
    # Set globals
    log_config_vars()

    # Initialize Layout
    layout.layout()

    # Run Server
    app.run_server(
        debug=ENV.DEBUG,
        host=ENV.WEB_SERVER_HOST,
        port=ENV.WEB_SERVER_PORT,
        # useful dev settings (these are enabled automatically when debug=True)
        dev_tools_silence_routes_logging=not ENV.DEBUG,
        use_reloader=ENV.DEBUG,
        dev_tools_hot_reload=ENV.DEBUG,
        # Flask.run() defaults `threaded=True`. Our session store (SimpleCache,
        # persisted via SESSION_REFRESH_EACH_REQUEST, which also defaults to True)
        # does a full read-modify-write of the whole session dict on every request,
        # with no locking -- under real thread concurrency, two overlapping requests
        # racing to save() can let a stale (e.g. pre-login) snapshot clobber a
        # newer one, silently wiping the just-set OIDC token. Force single-threaded
        # to make request handling serial and remove the race.
        threaded=False,
    )


if __name__ == "__main__":
    # Parse Args
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log", default="INFO", help="the output logging level")
    args = parser.parse_args()

    # Log
    if ENV.DEBUG:
        coloredlogs.install(level="DEBUG")
    else:
        coloredlogs.install(level=args.log.upper())
    logging.warning(args)

    # Go
    main()
