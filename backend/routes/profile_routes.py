from __future__ import annotations

from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from backend.auth import get_authenticated_user_id
from backend.security.encryption import get_active_dek
from backend.repositories.profile_repository import ProfileRepository


router = APIRouter(
    prefix="/api/profile",
    tags=["profile"],
)

profile_repo=ProfileRepository()
class ProfileResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str

    name: str = ""
    first_name: str = ""
    middle_name: str = ""
    last_name: str = ""

    dob: str = ""

    address: str = ""
    house_number: str = ""
    street: str = ""
    locality: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""

    guardian_name: str = ""
    place_of_birth: str = ""

    gender: str = ""
    year_of_birth: str = ""

    aadhaar_number: str = ""
    voter_id: str = ""
    birth_registration_number: str = ""


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None

    dob: Optional[str] = None

    address: Optional[str] = None
    house_number: Optional[str] = None
    street: Optional[str] = None
    locality: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    guardian_name: Optional[str] = None
    place_of_birth: Optional[str] = None

    gender: Optional[str] = None
    year_of_birth: Optional[str] = None

    aadhaar_number: Optional[str] = None
    voter_id: Optional[str] = None
    birth_registration_number: Optional[str] = None


@router.get(
    "/",
    response_model=ProfileResponse,
)
async def get_profile(
    user_id: ObjectId = Depends(get_authenticated_user_id),
):
    profile = profile_repo.get_by_user_id(user_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return profile


@router.put(
    "/",
    response_model=ProfileResponse,
)
async def update_profile(
    payload: ProfileUpdate,
    user_id: ObjectId = Depends(get_authenticated_user_id),
):
    profile = profile_repo.get_by_user_id(user_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    dek = get_active_dek()

    # Only values explicitly supplied by the frontend are updated.
    update_data = payload.model_dump(exclude_unset=True)

    merged_profile = profile.copy()
    merged_profile.update(update_data)

    try:
        updated = profile_repo.update_patient_profile(
            user_id=user_id,
            profile=merged_profile,
            dek=dek,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update profile",
        ) from exc

    return updated
