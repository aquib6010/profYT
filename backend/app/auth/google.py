"""Google OAuth Flow factory.

Centralizes scope list, redirect URI, and client credentials. The two
endpoints (/auth/google/login and /auth/google/callback) both call
build_flow() so the OAuth config exists in exactly one place.

SCOPES must EXACTLY match the scopes added on the Google Cloud Console
consent screen. If you change them here, also change them there or the
consent request will be rejected.

The monetary scope (`yt-analytics-monetary.readonly`) is what unlocks
revenue data. Without it, every endpoint that returns $ values comes
back empty — there's no fallback. Treat it as a hard requirement.
"""

from __future__ import annotations

import os

from app.config import get_settings

# oauthlib refuses to do the token exchange over plain HTTP unless this is set.
# In dev our redirect URI is http://localhost; in prod it must be https.
if get_settings().oauth_redirect_uri.startswith("http://"):
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

from google_auth_oauthlib.flow import Flow  # noqa: E402  (env var must be set first)

SCOPES: list[str] = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]

# Google's OIDC userinfo endpoint — called after token exchange to get the
# user's email, name, and stable `sub` identifier.
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def build_flow(state: str | None = None) -> Flow:
    """Construct a Google OAuth Flow configured from .env.

    Args:
        state: Optional CSRF state token. Pass on the callback so the Flow
            verifies that the inbound state matches what we sent to Google.
            On the initial /login call, leave None and let Flow generate one.
    """
    s = get_settings()
    if not s.google_client_id or not s.google_client_secret:
        raise RuntimeError(
            "GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET missing from .env. "
            "Set them via Google Cloud Console -> Credentials."
        )

    client_config = {
        "web": {
            "client_id": s.google_client_id,
            "client_secret": s.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [s.oauth_redirect_uri],
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state,
    )
    flow.redirect_uri = s.oauth_redirect_uri
    return flow
