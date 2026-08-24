from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/forms", tags=["forms"])


@router.get("/")
async def placeholder_form() -> dict[str, str]:
    return {"status": "placeholder", "message": "Form filling functionality will be added later."}
