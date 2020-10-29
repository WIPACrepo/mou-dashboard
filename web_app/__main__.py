"""Root python script for MoU Dashboard web application."""

import argparse
import logging

import coloredlogs  # type: ignore[import]

# local imports
from web_app.config import app, CONFIG, update_config_global

from . import layout


def main(debug: bool) -> None:
    """Start up application context."""
    update_config_global()

    layout.layout()

    # Run Server
    app.run_server(debug=debug, host="localhost", port=CONFIG["WEB_SERVER_PORT"])


if __name__ == "__main__":
    # Parse Args
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log", default="DEBUG", help="the output logging level")
    parser.add_argument("--no-debug", default=False, action="store_true")
    args = parser.parse_args()

    # Log
    coloredlogs.install(level=getattr(logging, args.log.upper()))
    main(not args.no_debug)
