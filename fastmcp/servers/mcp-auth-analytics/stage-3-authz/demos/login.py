"""Headless Keycloak login so the demo needs no manual clicks.

FastMCP's OAuth client normally opens a browser. Here we replace that with a
function that fetches the Keycloak login page, submits the username and
password, and follows the redirect back to the client's local callback.
Pass --interactive to a demo to use your real browser instead.
"""

import html
import logging
import os
import re
import threading
import warnings
from urllib.parse import urljoin

import httpx

from fastmcp import Client
from fastmcp.client.auth import OAuth
from fastmcp.client.auth.client_credentials import ClientCredentialsOAuthProvider

warnings.filterwarnings(
    "ignore"
)  # in-memory token storage notice is expected in a demo
logging.getLogger("fastmcp").setLevel(logging.WARNING)
os.environ.setdefault("FASTMCP_LOG_LEVEL", "WARNING")

REALM = "http://localhost:8080/realms/analytics-demo"


def _login(authorization_url: str, username: str, password: str) -> None:
    with httpx.Client(follow_redirects=False) as http:
        page = http.get(authorization_url)
        form = re.search(
            r'<form[^>]*id="kc-form-login"[^>]*action="([^"]+)"', page.text, re.S
        ) or re.search(r'<form[^>]*action="([^"]+)"', page.text, re.S)
        if not form:
            raise RuntimeError("Keycloak login form not found; is the realm imported?")

        # Keycloak marks its session cookies Secure even on http://localhost, which
        # browsers accept but httpx's jar will not send, so forward them by hand.
        def cookie_header():
            return {
                "Cookie": "; ".join(f"{c.name}={c.value}" for c in http.cookies.jar)
            }

        resp = http.post(
            html.unescape(form.group(1)),
            data={"username": username, "password": password},
            headers=cookie_header(),
        )
        # Follow redirects until we hit the client's http://localhost:<port>/callback.
        # Clients that identify with a Client ID Metadata Document get Keycloak's
        # consent screen on the way; accept it, as a user would.
        while True:
            while resp.is_redirect:
                target = urljoin(str(resp.url), resp.headers["location"])
                resp = http.get(target, headers=cookie_header())
                if target.startswith("http://localhost:") and "/callback" in target:
                    return
            consent = re.search(r'<form[^>]*action="([^"]+)"', resp.text, re.S)
            if (
                resp.status_code != 200
                or not consent
                or 'name="accept"' not in resp.text
            ):
                return
            resp = http.post(
                urljoin(str(resp.url), html.unescape(consent.group(1))),
                data={"accept": "Yes"},
                headers=cookie_header(),
            )


def oauth_for(user: str, password: str, interactive: bool = False) -> OAuth:
    """An OAuth provider whose browser step is replaced by a scripted login."""
    provider = OAuth(client_name=f"demo-{user}")
    if not interactive:

        async def redirect_handler(authorization_url: str) -> None:
            # The callback server is waiting in another task; do the login in a thread.
            threading.Thread(
                target=_login, args=(authorization_url, user, password), daemon=True
            ).start()

        provider.redirect_handler = redirect_handler  # type: ignore[method-assign]
    return provider


def bot_auth(server_url: str) -> ClientCredentialsOAuthProvider:
    return ClientCredentialsOAuthProvider(
        server_url,
        client_id="nightly-report-bot",
        client_secret="nightly-report-bot-secret",
        issuer=REALM,
    )


def as_user(url: str, user: str, interactive: bool = False) -> Client:
    return Client(url, auth=oauth_for(user, user, interactive))
