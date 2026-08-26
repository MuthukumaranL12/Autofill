from __future__ import annotations

import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.settings import get_settings


security = HTTPBearer(auto_error=False)


async def get_authenticated_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> ObjectId:
    if credentials is None:
        request.state.user_id = None
        raise HTTPException(status_code=401, detail="Authentication is required")

    token = credentials.credentials

    settings = get_settings()
    secret = settings.jwt_secret_key or "development-secret-change-me"
    algorithm = settings.jwt_algorithm or "HS256"
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
    except (jwt.InvalidTokenError, TypeError, ValueError) as exc:
        request.state.user_id = None
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        request.state.user_id = None
        raise HTTPException(status_code=401, detail="Token payload is missing user identity")

    try:
        user_obj_id = ObjectId(str(user_id))
    except Exception as exc:
        request.state.user_id = None
        raise HTTPException(status_code=401, detail="Invalid user identity in token") from exc

    request.state.user_id = user_obj_id
    return user_obj_id