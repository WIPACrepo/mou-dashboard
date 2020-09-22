"""Root python script for MoU Dashboard web application."""

import argparse
import logging

import coloredlogs  # type: ignore[import]

# local imports
from web_app.config import app, log_environment, WEB_SERVER_PORT

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--port", type=int, default=WEB_SERVER_PORT, help="port to bind"
    )
    parser.add_argument("-l", "--log", default="DEBUG", help="the output logging level")
    args = parser.parse_args()

    coloredlogs.install(level=getattr(logging, args.log.upper()))

    log_environment()

    if args.port != WEB_SERVER_PORT:
        logging.warning(f"USING PORT {args.port} (NOT {WEB_SERVER_PORT})")

    app.run_server(debug=True, host="localhost", port=args.port)
