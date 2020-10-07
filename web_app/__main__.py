"""Root python script for MoU Dashboard web application."""

import argparse
import logging

import coloredlogs  # type: ignore[import]
from flask import g

# local imports
from rest_tools.server.config import from_environment  # type: ignore[import]
from web_app.config import _CONFIG, app, log_config

if __name__ == "__main__":
    env = from_environment(_CONFIG)
    g.update(env)

    # Parse Args
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log", default="DEBUG", help="the output logging level")
    args = parser.parse_args()

    # Log
    coloredlogs.install(level=getattr(logging, args.log.upper()))
    log_config(env)

    # Run Server
    app.run_server(debug=True, host="localhost", port=g["WEB_SERVER_PORT"])
