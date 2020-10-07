"""Root python script for MoU Dashboard web application."""

import argparse
import logging

import coloredlogs  # type: ignore[import]

# local imports
from rest_tools.server.config import from_environment  # type: ignore[import]
from web_app.config import app, CONFIG, log_config

if __name__ == "__main__":
    CONFIG = from_environment(CONFIG)

    # Parse Args
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log", default="DEBUG", help="the output logging level")
    args = parser.parse_args()

    # Log
    coloredlogs.install(level=getattr(logging, args.log.upper()))
    log_config(CONFIG)

    # Run Server
    app.run_server(debug=True, host="localhost", port=CONFIG["WEB_SERVER_PORT"])
