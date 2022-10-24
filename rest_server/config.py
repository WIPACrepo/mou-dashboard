"""Config settings."""


import logging
import os
from typing import Any, Dict

# --------------------------------------------------------------------------------------
# Constants


DEFAULT_ENV_CONFIG = {
    "AUTH_AUDIENCE": "mou",
    "AUTH_OPENID_URL": "",
    "MOU_MONGODB_AUTH_USER": "",  # None means required to specify
    "MOU_MONGODB_AUTH_PASS": "",  # empty means no authentication required
    "MOU_MONGODB_HOST": "localhost",
    "MOU_MONGODB_PORT": "27017",
    "MOU_REST_HOST": "localhost",
    "MOU_REST_PORT": "8080",
}

AUTH_SERVICE_ACCOUNT = "mou-service-account"

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


def is_testing() -> bool:
    """
    Return true if this is the test environment.

    Note: this needs to run on import.
    """
    return bool(os.environ.get('CI_TEST_ENV', False))


def log_environment(config_env: Dict[str, Any]) -> None:
    """Log the environment variables."""
    for name in config_env:
        logging.info(f"{name} \t {config_env[name]}")
