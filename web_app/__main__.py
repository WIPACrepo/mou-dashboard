"""Root python script for MoU Dashboard web application."""

import argparse
import logging

# local imports
from web_app.config import app

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Find files under PATH(s), compute their metadata and "
        "upload it to File Catalog.",
        epilog="Notes: (1) symbolic links are never followed.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-p", "--port", type=int, default=8050, help="port to bind")
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)
    app.run_server(debug=True, host="localhost", port=args.port)
