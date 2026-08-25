from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId

from backend.security.encryption import ActiveDek, encrypt_text
from backend.security.hmac_utils import tokenise
from backend.database.mongodb import get_database


def _value(fields: dict, *names: str):
    for name in names:
        item = fields.get(name)
        if isinstance(item, dict) and item.get("value") is not None:
            return item["value"]
    return None


def build_profile_update(fields: dict, dek: ActiveDek) -> dict:
    update: dict = {"dek_id": dek.id, "updated_at": datetime.now(timezone.utc)}
    encrypted_fields = {
        "name_enc": _value(fields, "full_name", "child_full_name"),
        "dob_enc": _value(fields, "date_of_birth"),
        "address_enc": _value(fields, "address"),
        "guardian_name_enc": _value(fields, "father_or_husband_name", "father_name", "relative_name"),
        "place_of_birth_enc": _value(fields, "place_of_birth"),
    }
    for field_name, value in encrypted_fields.items():
        if value is not None:
            update[field_name] = encrypt_text(str(value))

    for target in ("gender", "blood_group", "year_of_birth", "nationality"):
        value = _value(fields, target)
        if value is not None:
            update[target] = value

    token_fields = {
        "aadhaar_token": "aadhaar_number",
        "pan_token": "pan_number",
        "voter_id_token": "epic_number",
        "driving_licence_token": "driving_licence_number",
        "passport_token": "passport_number",
        "birth_reg_token": "registration_number",
        "health_insurance_token": "member_id",
    }
    for target, source in token_fields.items():
        value = _value(fields, source)
        if value is not None:
            update[target] = tokenise(str(value))
    return update


def get_profile_id(user_id: ObjectId) -> ObjectId:
    collection = get_database().patient_profiles
    existing = collection.find_one({"user_id": user_id}, {"_id": 1})
    return existing["_id"] if existing else ObjectId()


def upsert_patient_profile(user_id: ObjectId, profile_id: ObjectId, fields: dict, dek: ActiveDek) -> ObjectId:
    collection = get_database().patient_profiles
    update = build_profile_update(fields, dek)
    update["user_id"] = user_id
    if "name_enc" not in update and not collection.find_one({"user_id": user_id}, {"_id": 1}):
        raise RuntimeError("A new patient profile requires an extracted name")
    collection.update_one(
        {"user_id": user_id},
        {"$set": update, "$setOnInsert": {"_id": profile_id, "created_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return profile_id