from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.auth_service import login_user, register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    phone: str
    password: str
    consent_given: bool = False


class LoginRequest(BaseModel):
    phone: str
    password: str


@router.post("/register", status_code=201)
async def register(payload: RegisterRequest) -> dict[str, str]:
    try:
        user_id = register_user(payload.phone, payload.password, payload.consent_given)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"user_id": str(user_id), "message": "User registered successfully"}


@router.post("/login")
async def login(payload: LoginRequest) -> dict[str, str]:
    try:
        token = login_user(payload.phone, payload.password)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {"access_token": token, "token_type": "bearer"}
