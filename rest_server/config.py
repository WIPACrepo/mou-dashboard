"""Config settings."""


EXPECTED_CONFIG = {
    "MOU_AUTH_ALGORITHM": "HS512",  # 'RS256',
    "MOU_AUTH_ISSUER": "http://localhost:8888",  # 'maddash',
    "MOU_AUTH_SECRET": "secret",
    "MOU_MONGODB_AUTH_USER": "",  # None means required to specify
    "MOU_MONGODB_AUTH_PASS": "",  # empty means no authentication required
    "MOU_MONGODB_HOST": "localhost",
    "MOU_MONGODB_PORT": "27017",
    "MOU_REST_HOST": "localhost",
    "MOU_REST_PORT": "8080",
}


AUTH_PREFIX = "mou"
