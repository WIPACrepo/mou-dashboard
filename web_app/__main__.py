"""Root python script for MoU Dashboard web application."""

import logging

# local imports
from web_app.config import app

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    app.run_server(debug=True)
