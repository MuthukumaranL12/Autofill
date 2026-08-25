from __future__ import annotations

from bson import ObjectId
from fastapi import HTTPException, Request


async def get_authenticated_user_id(request: Request) -> ObjectId:
    user_id = getattr(request.state, "user_id", None)
    if isinstance(user_id, ObjectId):
        return user_id
    if isinstance(user_id, str):
        try:
            return ObjectId(user_id)
        except Exception:
            pass
    raise HTTPException(status_code=401, detail="Authentication is required")