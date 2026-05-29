"""Shared FastAPI dependencies for authenticated endpoints.

`current_creator` is the single gate every data endpoint sits behind: it reads
the creator id off the signed session and loads the row, 401-ing if either is
missing. Keeps session-handling in one place instead of repeated in each route.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Creator


async def current_creator(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Creator:
    """Resolve the signed-in creator, or raise 401."""
    creator_id = request.session.get("creator_id")
    if not creator_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    creator = await session.get(Creator, creator_id)
    if creator is None:
        request.session.pop("creator_id", None)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    return creator
