"""Config file."""

import dataclasses as dc
import logging
import os
from typing import Final
from urllib.parse import urljoin

import dash  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import flask
import werkzeug
from cachelib import SimpleCache
from flask_oidc import OpenIDConnect  # type: ignore[import]
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
from wipac_dev_tools import from_environment_as_dataclass

AUTO_RELOAD_MINS = 15  # how often to auto-reload the page
MAX_CACHE_MINS = 5  # how often to expire a cache result

REDIRECT_WBS = "mo"  # which mou to go to by default when ambiguously redirecting


# --------------------------------------------------------------------------------------
# configure config_vars


@dc.dataclass(frozen=True)
class EnvConfig:
    """For storing environment variables, typed."""

    # pylint:disable=invalid-name
    REST_SERVER_URL: str = "http://localhost:8080"
    TOKEN_SERVER_URL: str = "http://localhost:8888"
    WEB_SERVER_HOST: str = "localhost"
    WEB_SERVER_PORT: int = 8050
    AUTH_PREFIX: str = "mou"
    TOKEN_REQUEST_URL: str = dc.field(init=False)
    TOKEN: str = ""
    FLASK_SECRET: str = "super-secret-flask-key"
    OIDC_CLIENT_SECRETS: str = "client_secrets.json"
    OVERWRITE_REDIRECT_URI: str = ""
    DEBUG: bool = False
    DEBUG_AS_PI: list[str] = dc.field(default_factory=list)
    LOG_REST_CALLS: bool = True

    CI_TEST: bool = False

    def __post_init__(self) -> None:
        # since our instance is frozen, we need to use `__setattr__`
        object.__setattr__(
            self,
            "TOKEN_REQUEST_URL",
            urljoin(self.TOKEN_SERVER_URL, f"token?scope={self.AUTH_PREFIX}:admin"),
        )


ENV: Final = from_environment_as_dataclass(EnvConfig)


def log_config_vars() -> None:
    """Log the global configuration variables, key-value."""
    for field in dc.fields(ENV):
        logging.info(
            f"{field.name}\t{getattr(ENV, field.name)}\t({type(getattr(ENV, field.name)).__name__})"
        )


# --------------------------------------------------------------------------------------
# Set-up Dash server

app = dash.Dash(
    __name__,
    server=flask.Flask(__name__),
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://codepen.io/chriddyp/pen/bWLwgP.css",
        "https://fonts.googleapis.com/css2?family=Syncopate",
        "https://fonts.googleapis.com/css2?family=Sarpanch",
        "https://fonts.googleapis.com/css2?family=Kanit:wght@200",
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.2/css/all.min.css",
    ],
)

# config
server = app.server
app.config.suppress_callback_exceptions = True
server.config.update(SECRET_KEY=ENV.FLASK_SECRET)

# Trust the (single) reverse proxy/ingress in front of this app for scheme/host/
# client-ip info. Without this, `request.url_root` (used throughout flask-oidc for
# post-login/-logout redirect targets) resolves to the plain-http backend address
# instead of the public https:// one, since Flask never sees the original scheme.
server.wsgi_app = ProxyFix(  # type: ignore[method-assign]
    server.wsgi_app, x_proto=1, x_host=1, x_for=1, x_port=1
)

# Store sessions server-side: the OIDC token + userinfo (needed for group-based
# auth) don't fit in a client-side cookie (browsers cap cookies at ~4096 bytes).
_session_cache = SimpleCache()
server.config.update(SESSION_TYPE="cachelib", SESSION_CACHELIB=_session_cache)
Session(server)

# The token is disappearing from the session between two requests that share the
# same pid and the same cookie/sid -- meaning the SimpleCache *store* itself is
# losing the entry. Wrap its get/set/delete directly to see every read, write,
# and eviction, since reasoning about cachelib's internals from the outside
# hasn't explained it.
_orig_cache_get = _session_cache.get
_orig_cache_set = _session_cache.set
_orig_cache_delete = _session_cache.delete


def _traced_cache_get(key: str) -> object:
    value = _orig_cache_get(key)
    logging.info(
        f"SESSION-STORE pid={os.getpid()} GET key={key!r} found={value is not None} "
        f"has_token={bool((value or {}).get('oidc_auth_token'))} "
        f"cache_size={len(_session_cache._cache)}"
    )
    return value


def _traced_cache_set(key: str, value: object, timeout: object = None) -> object:
    logging.info(
        f"SESSION-STORE pid={os.getpid()} SET key={key!r} "
        f"has_token={bool((value or {}).get('oidc_auth_token'))} "
        f"cache_size_before={len(_session_cache._cache)}"
    )
    return _orig_cache_set(key, value, timeout=timeout)


def _traced_cache_delete(key: str) -> object:
    logging.info(f"SESSION-STORE pid={os.getpid()} DELETE key={key!r}")
    return _orig_cache_delete(key)


_session_cache.get = _traced_cache_get  # type: ignore[method-assign]
_session_cache.set = _traced_cache_set  # type: ignore[method-assign]
_session_cache.delete = _traced_cache_delete  # type: ignore[method-assign]


# --------------------------------------------------------------------------------------
# configure keycloak login

# from https://gist.github.com/thomasdarimont/145dc9aa857b831ff2eff221b79d179a
server.config.update(
    {
        # "TESTING": True,
        # "DEBUG": True,
        "OIDC_CLIENT_SECRETS": ENV.OIDC_CLIENT_SECRETS,
        # "OIDC_ID_TOKEN_COOKIE_SECURE": False, # default: True
        # "OIDC_REQUIRE_VERIFIED_EMAIL": True,  # default: False
        # "OIDC_USER_INFO_ENABLED": True, # default: True
        # "OIDC_OPENID_REALM": "flask-demo", # default: None
        # "OIDC_SCOPES": ["openid", "email", "profile"], # default: ["openid", "email"]
        # "OIDC_INTROSPECTION_AUTH_METHOD": "client_secret_post",  # default: client_secret_post
        "OIDC_OVERWRITE_REDIRECT_URI": ENV.OVERWRITE_REDIRECT_URI,
    }
)
oidc = OpenIDConnect(server)  # grabs "OIDC_CLIENT_SECRETS"/ENV.OIDC_CLIENT_SECRETS

# flask-oidc's before_request hook (`check_token_expiry`) silently tries to refresh
# the access token on *every* request and fires no signal of its own -- it's the
# last unaccounted-for code path that writes to `session["oidc_auth_token"]`
# (besides login/logout, which we already log). Wrap it to see directly whether
# it's the one clearing the token, and why (e.g. a bad/missing `expires_at`).
_orig_check_token_expiry = oidc.check_token_expiry


def _traced_check_token_expiry() -> flask.Response | None:  # type: ignore[name-defined]
    token_before = flask.session.get("oidc_auth_token") or {}
    result = _orig_check_token_expiry()
    token_after = flask.session.get("oidc_auth_token") or {}
    if token_before.get("access_token") != token_after.get("access_token"):
        logging.warning(
            f"OIDC: pid={os.getpid()} check_token_expiry CHANGED session token on "
            f"{flask.request.path!r} -- "
            f"before(has_token={bool(token_before)}, expires_at={token_before.get('expires_at')!r}, "
            f"expires_in={token_before.get('expires_in')!r}) -> "
            f"after(has_token={bool(token_after)}) redirected={result is not None!r}"
        )
    return result


oidc.check_token_expiry = _traced_check_token_expiry


@server.after_request  # type: ignore[misc]
def _log_auth_redirects(
    response: werkzeug.wrappers.response.Response,  # type: ignore[name-defined]
) -> werkzeug.wrappers.response.Response:  # type: ignore[name-defined]
    """Log every server-side (HTTP) redirect, to help diagnose login/logout loops.

    Dash's own page navigation (e.g. '/' -> '/mo') happens client-side via JS and
    never shows up here. Only real HTTP redirects do: the OIDC login/authorize/
    logout hops -- notably including flask-oidc's *forced* logout when it can't
    refresh an access token, which fires no signal of its own and would
    otherwise be invisible.

    Scheme/proto/cookie-presence were added to rule out a reverse-proxy scheme
    bug; that's now confirmed fine. `pid` and `cookie_sid` are here to catch a
    *different* culprit: `SimpleCache` (our session store, config'd above) is
    documented as "for single process environments" only -- if this pod runs
    more than one worker process, each has its own private copy of the session
    store, and a session written by one worker is invisible to another.
    """
    if 300 <= response.status_code < 400:
        cookie_val = flask.request.cookies.get("session")
        cookie_sid_prefix = cookie_val[:12] if cookie_val else None
        logging.info(
            f"AUTH-REDIRECT pid={os.getpid()} {flask.request.method} {flask.request.path} -> "
            f"{response.status_code} Location={response.location!r} "
            f"oidc_token={'present' if flask.session.get('oidc_auth_token') else 'absent'} "
            f"scheme={flask.request.scheme!r} "
            f"x_forwarded_proto={flask.request.headers.get('X-Forwarded-Proto')!r} "
            f"has_cookie={'session' in flask.request.cookies} "
            f"cookie_sid={cookie_sid_prefix!r}"
        )
    return response


@server.route("/invalid-permissions")  # type: ignore[misc]
def invalid_permissions() -> str | werkzeug.wrappers.response.Response:  # type: ignore[name-defined]
    """Redirected to tell the user they can't do anything other than logout."""
    logging.critical("/invalid-permissions")
    return (
        'You don\'t have valid permissions to edit MOUs. <a href="/logout">Logout</a>'
    )
