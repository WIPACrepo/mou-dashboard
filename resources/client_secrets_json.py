"""Script to create an OIDC client_secrets.json file."""

import json
import os


def main() -> None:
    """Write .json from env vars."""

    realm = os.environ["KEYCLOAK_REALM"]
    url = os.environ["KEYCLOAK_URL"]

    client_secrets = {
        "web": {
            "issuer": f"{url}/auth/realms/{realm}",
            "auth_uri": f"{url}/auth/realms/{realm}/protocol/openid-connect/auth",
            "client_id": os.environ["KEYCLOAK_CLIENT_ID"],
            "client_secret": os.environ["KEYCLOAK_CLIENT_SECRET"],
            "redirect_uris": ["https://mou.icecube.aq/*"],
            "userinfo_uri": f"{url}/auth/realms/{realm}/protocol/openid-connect/userinfo",
            "token_uri": f"{url}/auth/realms/{realm}/protocol/openid-connect/token",
            "token_introspection_uri": f"{url}/auth/realms/{realm}/protocol/openid-connect/token/introspect",
        }
    }

    with open("client_secrets.json", "w") as f:
        json.dump(client_secrets, f, indent=4)


if __name__ == "__main__":
    main()
