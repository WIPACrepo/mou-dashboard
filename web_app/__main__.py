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
        debug=bool(ENV.DEBUG),
        host=ENV.WEB_SERVER_HOST,
        port=ENV.WEB_SERVER_PORT,
        # useful dev settings (these are enabled automatically when debug=True)
        dev_tools_silence_routes_logging=True,
        use_reloader=True,
        dev_tools_hot_reload=True,
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
