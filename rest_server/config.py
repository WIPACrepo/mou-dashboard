"""Config settings."""


import logging

# local imports
from rest_tools.server.config import from_environment  # type: ignore[import]

# --------------------------------------------------------------------------------------
# Get constants from environment variables


_config_env = from_environment(
    {
        "MOU_AUTH_ALGORITHM": "HS512",  # 'RS256',
        "MOU_AUTH_ISSUER": "http://localhost:8888",  # 'maddash',
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


MOU_AUTH_ALGORITHM = _config_env["MOU_AUTH_ALGORITHM"]
MOU_AUTH_ISSUER = _config_env["MOU_AUTH_ISSUER"]
MOU_AUTH_SECRET = _config_env["MOU_AUTH_SECRET"]
MOU_AUTH_PREFIX = _config_env["MOU_AUTH_PREFIX"]


def log_environment() -> None:
    """Log the environment variables."""
    for name in _config_env:
        logging.info(f"{name} \t {_config_env[name]}")
