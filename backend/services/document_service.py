from __future__ import annotations

from bson import ObjectId

from backend.security.encryption import get_active_dek
from backend.database.repositories.patient_profiles import get_profile_id, upsert_patient_profile
from backend.database.repositories.source_documents import insert_source_document


def persist_extraction(user_id: ObjectId, extraction: dict) -> dict[str, ObjectId]:
    dek = get_active_dek()
    profile_id = get_profile_id(user_id)
    source_document_id = insert_source_document(user_id, profile_id, extraction)
    upsert_patient_profile(user_id, profile_id, extraction.get("extracted_fields", {}), dek)
    return {"source_document_id": source_document_id, "profile_id": profile_id}