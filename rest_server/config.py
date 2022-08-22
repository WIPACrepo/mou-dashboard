"""Config settings."""


import dataclasses as dc
import logging
from typing import Any, Dict

# --------------------------------------------------------------------------------------
# Constants


@dc.dataclass(frozen=True)
class EnvConfig:
    """Environment variables."""

    # pylint:disable=invalid-name
    MOU_AUTH_ALGORITHM: str = "HS512"  # 'RS256',
    MOU_AUTH_ISSUER: str = "http://localhost:8888"  # 'MOUdash',
    MOU_AUTH_SECRET: str = "secret"
    MOU_MONGODB_AUTH_USER: str = ""  # None means required to specify
    MOU_MONGODB_AUTH_PASS: str = ""  # empty means no authentication required
    MOU_MONGODB_HOST: str = "localhost"
    MOU_MONGODB_PORT: int = 27017
    MOU_REST_HOST: str = "localhost"
    MOU_REST_PORT: int = 8080


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
