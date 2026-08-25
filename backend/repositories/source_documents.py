from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId

from backend.database.mongodb import get_database


SENSITIVE_FIELDS = {
    "aadhaar_number",
    "pan_number",
    "epic_number",
    "driving_licence_number",
    "passport_number",
    "registration_number",
    "member_id",
    "mobile_number",
    "phone_number",
    "policy_number",
    "insurance_id",
    "card_number",
    "claim_number",
    "customer_id",
    "file_number",
    "personal_number",
}


def redact_sensitive_extraction(extraction: dict) -> dict:
    sanitized = dict(extraction)
    source_fields = extraction.get("extracted_fields", {}) or {}
    redacted_fields = {}
    for key, value in source_fields.items():
        if isinstance(value, dict):
            redacted = dict(value)
            if (
                key in SENSITIVE_FIELDS
                or "_number" in key
                or "phone" in key.lower()
                or "mobile" in key.lower()
            ):
                redacted["value"] = None
                redacted["confidence"] = 0.0
            redacted_fields[key] = redacted
    sanitized["extracted_fields"] = redacted_fields
    return sanitized


def insert_source_document(user_id: ObjectId, profile_id: ObjectId, extraction: dict) -> ObjectId:
    now = datetime.now(timezone.utc)
    sanitized_extraction = redact_sensitive_extraction(extraction)
    record = {
        "user_id": user_id,
        "profile_id": profile_id,
        "doc_type": extraction["document_type"],
        "source": "gemini",
        "s3_key_enc": "",
        "ocr_status": "success",
        "confidence_score": extraction["overall_confidence"],
        "manual_review_required": False,
        "manual_verified_by": None,
        "gemini_raw_response": sanitized_extraction,
        "textract_raw_response": None,
        "extracted_fields_snapshot": sanitized_extraction.get("extracted_fields", {}),
        "uploaded_at": now,
        "processed_at": now,
    }
    return get_database().source_documents.insert_one(record).inserted_id