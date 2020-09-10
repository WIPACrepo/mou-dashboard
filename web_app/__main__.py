"""Root python script for MoU Dashboard web application."""

import argparse
import logging

# local imports
from web_app.config import app, log_environment, WEB_SERVER_PORT

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Find files under PATH(s), compute their metadata and "
        "upload it to File Catalog.",
        epilog="Notes: (1) symbolic links are never followed.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-p", "--port", type=int, default=WEB_SERVER_PORT, help="port to bind")
    parser.add_argument("-l", "--log", default="DEBUG", help="the output logging level")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log.upper()))
    log_environment()
    if args.port != WEB_SERVER_PORT:
        logging.warning(f"USING PORT {args.port} (NOT {WEB_SERVER_PORT})")
    app.run_server(debug=True, host="localhost", port=args.port)
