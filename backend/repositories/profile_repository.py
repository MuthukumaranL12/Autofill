from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId

from backend.database.mongodb import get_database
from backend.security.encryption import encrypt_text
from backend.security.hmac_utils import tokenise
from backend.security.decryption import decrypt_field


class ProfileRepository:

    def __init__(self):
        self.collection = get_database().patient_profiles

    # ---------------------------------------------------------
    # EXISTING METHOD
    # ---------------------------------------------------------

    def get_by_user_id(self, user_id):

        query = {
            "user_id": ObjectId(user_id)
        }

        profile = self.collection.find_one(query)
        print(profile)

        if not profile:
            raise ValueError("Identity profile not found")

        return self._to_profile_response(profile)

    # ---------------------------------------------------------
    # CONVERT MONGO DOCUMENT TO PROFILE RESPONSE
    # ---------------------------------------------------------

    def _to_profile_response(self, profile):
        """
        Convert the encrypted MongoDB document into the
        decrypted structure expected by the API/frontend.
        """

        return {
            "id": str(profile["_id"]),
            "user_id": str(profile["user_id"]),

            "name": self._decrypt(profile.get("name_enc")),
            "first_name": self._decrypt(
                profile.get("first_name_enc")
            ),
            "middle_name": self._decrypt(
                profile.get("middle_name_enc")
            ),
            "last_name": self._decrypt(
                profile.get("last_name_enc")
            ),

            "dob": self._decrypt(
                profile.get("dob_enc")
            ),

            "address": self._decrypt(
                profile.get("address_enc")
            ),
            "house_number": self._decrypt(
                profile.get("house_number_enc")
            ),
            "street": self._decrypt(
                profile.get("street_enc")
            ),
            "locality": self._decrypt(
                profile.get("locality_enc")
            ),
            "city": self._decrypt(
                profile.get("city_enc")
            ),
            "state": self._decrypt(
                profile.get("state_enc")
            ),
            "pincode": self._decrypt(
                profile.get("pincode_enc")
            ),

            "guardian_name": self._decrypt(
                profile.get("guardian_name_enc")
            ),
            "place_of_birth": self._decrypt(
                profile.get("place_of_birth_enc")
            ),

            "gender": profile.get("gender", "") or "",

            "year_of_birth": str(
                profile.get("year_of_birth", "") or ""
            ),

            "aadhaar_number": self._decrypt(
                profile.get("aadhaar_enc")
            ),

            "voter_id": self._decrypt(
                profile.get("voter_id_enc")
            ),

            "birth_registration_number": self._decrypt(
                profile.get("birth_reg_enc")
            ),
        }

    # ---------------------------------------------------------
    # DECRYPT HELPER
    # ---------------------------------------------------------

    @staticmethod
    def _decrypt(value):
        if value is None:
            return ""

        if isinstance(value, str):
            return value

        return decrypt_field(value)

    # ---------------------------------------------------------
    # UPDATE PROFILE
    # ---------------------------------------------------------

    def update_by_user_id(
        self,
        user_id,
        profile_data: dict
    ):
        """
        Update profile fields while preserving the existing
        encrypted MongoDB schema.
        """

        user_id = ObjectId(user_id)

        existing = self.collection.find_one(
            {"user_id": user_id}
        )

        if not existing:
            raise ValueError(
                "Identity profile not found"
            )

        update = {
            "updated_at": datetime.now(timezone.utc)
        }

        # -----------------------------------------------------
        # ENCRYPTED FIELDS
        # -----------------------------------------------------

        encrypted_fields = {
            "name": "name_enc",
            "first_name": "first_name_enc",
            "middle_name": "middle_name_enc",
            "last_name": "last_name_enc",

            "dob": "dob_enc",

            "address": "address_enc",
            "house_number": "house_number_enc",
            "street": "street_enc",
            "locality": "locality_enc",
            "city": "city_enc",
            "state": "state_enc",
            "pincode": "pincode_enc",

            "guardian_name": "guardian_name_enc",
            "place_of_birth": "place_of_birth_enc",

            "aadhaar_number": "aadhaar_enc",
            "voter_id": "voter_id_enc",
            "birth_registration_number": "birth_reg_enc",
        }

        for frontend_field, db_field in encrypted_fields.items():

            if frontend_field not in profile_data:
                continue

            value = profile_data[frontend_field]

            if value is None:
                continue

            value = str(value).strip()

            update[db_field] = encrypt_text(value)

        # -----------------------------------------------------
        # NON-ENCRYPTED FIELDS
        # -----------------------------------------------------

        if "gender" in profile_data:

            gender = profile_data["gender"]

            if gender is not None:
                gender = str(gender).strip()

                if gender.lower() in {"male", "m"}:
                    gender = "MALE"

                elif gender.lower() in {
                    "female",
                    "f"
                }:
                    gender = "FEMALE"

                elif gender.lower() == "other":
                    gender = "OTHER"

                update["gender"] = gender

        if "year_of_birth" in profile_data:

            value = profile_data["year_of_birth"]

            if value is not None:
                update["year_of_birth"] = str(
                    value
                ).strip()

        # -----------------------------------------------------
        # UPDATE HMAC TOKENS
        # -----------------------------------------------------

        identifier_tokens = {
            "aadhaar_number": "aadhaar_token",
            "voter_id": "voter_id_token",
            "birth_registration_number":
                "birth_reg_token",
        }

        for frontend_field, db_field in identifier_tokens.items():

            if frontend_field not in profile_data:
                continue

            value = profile_data[frontend_field]

            if value is None:
                continue

            value = str(value).strip()

            if value:
                update[db_field] = tokenise(value)

        # -----------------------------------------------------
        # SAVE
        # -----------------------------------------------------

        self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": update
            }
        )

        # Return the decrypted representation
        return self.get_by_user_id(user_id)