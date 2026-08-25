from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pymongo import MongoClient


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256").strip()
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/medform_db").strip()
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "medform_db").strip()

if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is not set")

_mongo_client = MongoClient(MONGODB_URI)
_users_collection = _mongo_client[MONGODB_DB_NAME]["users"]

def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=JWT_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": expires_at,
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        subject = payload.get("sub")
        if not subject:
            raise credentials_exception

        user_id = ObjectId(subject)
    except (JWTError, TypeError, ValueError):
        raise credentials_exception

    user = _users_collection.find_one(
        {"_id": user_id, "is_active": True},
        {"password_hash": 0},
    )
    if user is None:
        raise credentials_exception

    return {"id": str(user["_id"]), "role": user.get("role")}
