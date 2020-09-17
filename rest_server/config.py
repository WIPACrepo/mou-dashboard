"""Config settings."""


import logging
from urllib.parse import quote_plus

# local imports
from rest_tools.server.config import from_environment  # type: ignore[import]

# --------------------------------------------------------------------------------------
# Get constants from environment variables


_config_env = from_environment(
    {
        "MOU_AUTH_ALGORITHM": "HS512",  # 'RS256',
        "MOU_AUTH_ISSUER": "http://localhost:8888",  # 'MOUdash',
        "MOU_AUTH_SECRET": "secret",
        "MOU_MONGODB_AUTH_USER": "",  # None means required to specify
        "MOU_MONGODB_AUTH_PASS": "",  # empty means no authentication required
        "MOU_MONGODB_HOST": "localhost",
        "MOU_MONGODB_PORT": "27017",
        "MOU_REST_HOST": "localhost",
        "MOU_REST_PORT": "8080",
        "MOU_AUTH_PREFIX": "mou",
    }
)


AUTH_ALGORITHM = _config_env["MOU_AUTH_ALGORITHM"]
AUTH_ISSUER = _config_env["MOU_AUTH_ISSUER"]
AUTH_SECRET = _config_env["MOU_AUTH_SECRET"]
AUTH_PREFIX = _config_env["MOU_AUTH_PREFIX"]
REST_HOST = _config_env["MOU_REST_HOST"]
REST_PORT = int(_config_env["MOU_REST_PORT"])
MONGODB_AUTH_USER = quote_plus(_config_env["MOU_MONGODB_AUTH_USER"])
MONGODB_AUTH_PASS = quote_plus(_config_env["MOU_MONGODB_AUTH_PASS"])
MONGODB_HOST = _config_env["MOU_MONGODB_HOST"]
MONGODB_PORT = int(_config_env["MOU_MONGODB_PORT"])

EXCLUDE_DBS = [
    "system.indexes",
    "production",
    "local",
    "simprod_filecatalog",
    "config",
    "token_service",
    "admin",
]


def log_environment() -> None:
    """Log the environment variables."""
    for name in _config_env:
        logging.info(f"{name} \t {_config_env[name]}")
