from pydantic import BaseModel
from typing import Optional


class IdentityProfile(BaseModel):

    name: Optional[str] = ""

    dob: Optional[str] = ""

    address: Optional[str] = ""

    guardian_name: Optional[str] = ""

    place_of_birth: Optional[str] = ""

    gender: Optional[str] = ""

    year_of_birth: Optional[str] = ""

    aadhaar_number: Optional[str] = ""

    voter_id: Optional[str] = ""

    birth_registration_number: Optional[str] = ""