"""OAuth endpoints — login + callback.

Flow:
  GET /auth/google/login
    -> build Flow, generate auth URL + CSRF state
    -> stash state in signed-cookie session
    -> 302 redirect to Google's consent screen

  GET /auth/google/callback
    -> CSRF check: state must match what we stashed
    -> exchange auth code for access_token + refresh_token
    -> fetch /userinfo to get sub/email/name
    -> fetch YouTube channels.list?mine=true to get channel_id
    -> upsert Creator, encrypt + store tokens
    -> set creator_id in session, 302 to frontend /dashboard

Errors are surfaced as a redirect to /login?error=... rather than a JSON 4xx,
so the user lands somewhere with a UI instead of a raw error response.
"""

from __future__ import annotations

import logging
from datetime import UTC

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
from starlette.responses import RedirectResponse

from app.auth.crypto import encrypt_token
from app.auth.google import USERINFO_URL, build_flow
from app.config import get_settings
from app.db import get_session
from app.models import Creator

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/google", tags=["auth"])

YT_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """Start the OAuth flow — sends the user to Google's consent screen."""
    flow = build_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",          # Issues a refresh_token so we can renew silently.
        include_granted_scopes="true",  # Incremental consent.
        prompt="consent",               # Force consent so refresh_token is reliably issued.
    )
    request.session["oauth_state"] = state
    return RedirectResponse(auth_url, status_code=302)


@router.get("/callback")
async def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """Handle Google's redirect, upsert the creator, sign them in."""
    settings = get_settings()
    frontend = settings.frontend_origin

    # --- User denied consent or Google reported an error ---
    if error:
        log.warning("OAuth error from Google: %s", error)
        return RedirectResponse(f"{frontend}/login?error={error}", status_code=302)

    if not code or not state:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing code or state")

    # --- 1. CSRF state check ---
    stashed = request.session.pop("oauth_state", None)
    if not stashed or stashed != state:
        log.warning("OAuth state mismatch (CSRF). got=%r expected=%r", state, stashed)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid OAuth state (CSRF)")

    # --- 2. Exchange auth code for tokens ---
    flow = build_flow(state=state)
    try:
        # fetch_token is synchronous (uses requests); push it off the event loop.
        await run_in_threadpool(flow.fetch_token, authorization_response=str(request.url))
    except Exception:
        log.exception("Token exchange failed")
        return RedirectResponse(
            f"{frontend}/login?error=token_exchange_failed", status_code=302
        )

    creds = flow.credentials
    access_token = creds.token
    refresh_token = creds.refresh_token  # may be None on re-login if `prompt=consent` was skipped
    expiry = creds.expiry.replace(tzinfo=UTC) if creds.expiry else None

    # --- 3 + 4. Userinfo and YouTube channel lookup (one HTTP client) ---
    async with httpx.AsyncClient(timeout=10.0) as client:
        ui_resp = await client.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if ui_resp.status_code != 200:
            log.warning("/userinfo returned %s: %s", ui_resp.status_code, ui_resp.text[:200])
            return RedirectResponse(
                f"{frontend}/login?error=userinfo_{ui_resp.status_code}", status_code=302
            )
        userinfo = ui_resp.json()
        sub = userinfo.get("sub")
        email = userinfo.get("email")
        name = userinfo.get("name")
        if not sub or not email:
            return RedirectResponse(
                f"{frontend}/login?error=userinfo_incomplete", status_code=302
            )

        ch_resp = await client.get(
            YT_CHANNELS_URL,
            params={"mine": "true", "part": "id,snippet"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if ch_resp.status_code != 200:
            log.warning("channels.list returned %s: %s", ch_resp.status_code, ch_resp.text[:200])
            return RedirectResponse(
                f"{frontend}/login?error=youtube_api_{ch_resp.status_code}",
                status_code=302,
            )
        items = ch_resp.json().get("items", [])
        if not items:
            return RedirectResponse(
                f"{frontend}/login?error=no_youtube_channel", status_code=302
            )
        channel_id = items[0]["id"]

    # --- 5. Upsert the Creator row ---
    result = await session.execute(select(Creator).where(Creator.google_sub == sub))
    creator = result.scalar_one_or_none()

    if creator is None:
        creator = Creator(google_sub=sub)
        session.add(creator)

    creator.email = email
    creator.display_name = name
    creator.channel_id = channel_id
    creator.access_token_enc = encrypt_token(access_token)
    if refresh_token:
        creator.refresh_token_enc = encrypt_token(refresh_token)
    creator.token_expires_at = expiry

    await session.commit()
    await session.refresh(creator)

    # --- 6. Sign them in and bounce to the dashboard ---
    request.session["creator_id"] = creator.id
    log.info("Signed in creator id=%s email=%s channel=%s", creator.id, email, channel_id)
    return RedirectResponse(f"{frontend}/dashboard", status_code=302)


@router.get("/me")
async def me(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    """Return the currently signed-in creator, or 401 if there's no session.

    The frontend calls this on load (with credentials) to decide whether to
    show the dashboard or bounce to /login. Returns only non-sensitive fields —
    never the encrypted tokens.
    """
    creator_id = request.session.get("creator_id")
    if not creator_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")

    creator = await session.get(Creator, creator_id)
    if creator is None:
        # Session points at a creator that no longer exists — clear it.
        request.session.pop("creator_id", None)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")

    return {
        "id": creator.id,
        "email": creator.email,
        "display_name": creator.display_name,
        "channel_id": creator.channel_id,
    }


@router.post("/logout")
async def logout(request: Request) -> dict[str, bool]:
    """Clear the session. Idempotent — safe to call when already signed out."""
    request.session.clear()
    return {"ok": True}
