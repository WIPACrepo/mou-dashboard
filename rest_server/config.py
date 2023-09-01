"""Config settings."""

import dataclasses as dc

from wipac_dev_tools import from_environment_as_dataclass

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
    CI_TEST: bool = False


ENV = from_environment_as_dataclass(EnvConfig)


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


def is_testing() -> bool:
    """Return true if this is the test environment.

    Note: this needs to run on import.
    """
    return ENV.CI_TEST
