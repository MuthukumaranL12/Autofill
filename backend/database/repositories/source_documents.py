from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId

from backend.database.mongodb import get_database


def insert_source_document(user_id: ObjectId, profile_id: ObjectId, extraction: dict) -> ObjectId:
    now = datetime.now(timezone.utc)
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
        "gemini_raw_response": extraction,
        "textract_raw_response": None,
        "extracted_fields_snapshot": extraction.get("extracted_fields", {}),
        "uploaded_at": now,
        "processed_at": now,
    }
    return get_database().source_documents.insert_one(record).inserted_id