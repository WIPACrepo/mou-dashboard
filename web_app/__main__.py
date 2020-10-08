"""Root python script for MoU Dashboard web application."""

import argparse
import logging

import coloredlogs  # type: ignore[import]

# local imports
from web_app.config import app, CONFIG, update_config_global


def main() -> None:
    """Start up application context."""
    update_config_global()

    # Run Server
    app.run_server(debug=True, host="localhost", port=CONFIG["WEB_SERVER_PORT"])


if __name__ == "__main__":
    # Parse Args
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log", default="DEBUG", help="the output logging level")
    args = parser.parse_args()

    # Log
    coloredlogs.install(level=getattr(logging, args.log.upper()))
    main()
