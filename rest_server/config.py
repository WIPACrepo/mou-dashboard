"""Config settings."""


import logging
from typing import Any, Dict

# --------------------------------------------------------------------------------------
# Constants


DEFAULT_ENV_CONFIG = {
    "MOU_AUTH_ALGORITHM": "HS512",  # 'RS256',
    "MOU_AUTH_ISSUER": "http://localhost:8888",  # 'MOUdash',
    "MOU_AUTH_SECRET": "secret",
    "MOU_MONGODB_AUTH_USER": "",  # None means required to specify
    "MOU_MONGODB_AUTH_PASS": "",  # empty means no authentication required
    "MOU_MONGODB_HOST": "localhost",
    "MOU_MONGODB_PORT": "27017",
    "MOU_REST_HOST": "localhost",
    "MOU_REST_PORT": "8080",
}

AUTH_PREFIX = "mou"

EXCLUDE_DBS = [
    "system.indexes",
    "production",
    "local",
    "simprod_filecatalog",
    "config",
    "token_service",
    "admin",
]

EXCLUDE_COLLECTIONS = ["system.indexes"]

SNAPSHOTS_DB = "SnapshotsDB"


def log_environment(config_env: Dict[str, Any]) -> None:
    """Log the environment variables."""
    for name in config_env:
        logging.info(f"{name} \t {config_env[name]}")
