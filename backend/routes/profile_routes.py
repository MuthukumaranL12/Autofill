from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/")
async def placeholder_profile() -> dict[str, str]:
    return {"status": "placeholder", "message": "Profile functionality will be added later."}
