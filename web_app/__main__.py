"""Root python script for MoU Dashboard web application."""

import argparse
import logging

import coloredlogs  # type: ignore[import]

# local imports
from web_app.config import app, CONFIG, log_config

if __name__ == "__main__":
    # Parse Args
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=CONFIG["WEB_SERVER_PORT"],
        help="port to bind",
    )
    parser.add_argument("-l", "--log", default="DEBUG", help="the output logging level")
    args = parser.parse_args()

    # Log
    coloredlogs.install(level=getattr(logging, args.log.upper()))
    log_config()
    if args.port != CONFIG["WEB_SERVER_PORT"]:
        logging.warning(f"USING PORT {args.port} (NOT {CONFIG['WEB_SERVER_PORT']})")

    # Run Server
    app.run_server(debug=True, host="localhost", port=args.port)
