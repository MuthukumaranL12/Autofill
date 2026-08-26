from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from bson import Binary, ObjectId
from fastapi.testclient import TestClient
from starlette.requests import Request
import asyncio

from backend.app import app
from backend.auth import get_authenticated_user_id, security
from backend.repositories.patient_profiles import build_profile_update
from backend.repositories.source_documents import redact_sensitive_extraction
from backend.document_extraction.gemini_service import GeminiExtractionService
from backend.services.auth_service import create_access_token, login_user, register_user


@pytest.fixture
def service() -> GeminiExtractionService:
    settings = SimpleNamespace(
        gemini_api_key="test-key",
        gemini_model="gemini-2.5-flash",
        gemini_api_version="v1alpha",
        upload_dir=Path("/tmp/test_uploads"),
        results_dir=Path("/tmp/test_results"),
    )
    return GeminiExtractionService(settings)


def _make_payload(document_type: str, field_name: str, value: str, confidence: float = 0.99):
    return {
        "status": "success",
        "document_type": document_type,
        "overall_confidence": confidence,
        "extracted_fields": {
            field_name: {"value": value, "confidence": confidence},
        },
    }


def test_aadhaar_response_normalization(service):
    result = service._normalize_payload(_make_payload("aadhaar", "full_name", "Muthukumaran L"))
    assert result["status"] == "success"
    assert result["document_type"] == "aadhaar"
    assert result["extracted_fields"]["full_name"]["value"] == "Muthukumaran L"
    assert result["extracted_fields"]["full_name"]["confidence"] == 0.99


def test_pan_response_normalization(service):
    result = service._normalize_payload(_make_payload("pan_card", "pan_number", "ABCDE1234F"))
    assert result["status"] == "success"
    assert result["document_type"] == "pan_card"
    assert result["extracted_fields"]["pan_number"]["value"] == "ABCDE1234F"


def test_passport_response_normalization(service):
    result = service._normalize_payload(_make_payload("passport", "passport_number", "P1234567"))
    assert result["status"] == "success"
    assert result["document_type"] == "passport"
    assert result["extracted_fields"]["passport_number"]["value"] == "P1234567"


def test_driving_licence_response_normalization(service):
    result = service._normalize_payload(_make_payload("driving_licence", "driving_licence_number", "DL-123456"))
    assert result["status"] == "success"
    assert result["document_type"] == "driving_licence"
    assert result["extracted_fields"]["driving_licence_number"]["value"] == "DL-123456"


def test_voter_id_response_normalization(service):
    result = service._normalize_payload(_make_payload("voter_id", "epic_number", "AB1234567"))
    assert result["status"] == "success"
    assert result["document_type"] == "voter_id"
    assert result["extracted_fields"]["epic_number"]["value"] == "AB1234567"


def test_birth_certificate_response_normalization(service):
    result = service._normalize_payload(_make_payload("birth_certificate", "child_full_name", "Ananya S"))
    assert result["status"] == "success"
    assert result["document_type"] == "birth_certificate"
    assert result["extracted_fields"]["child_full_name"]["value"] == "Ananya S"


def test_health_insurance_card_response_normalization(service):
    result = service._normalize_payload(_make_payload("health_insurance_card", "policy_number", "POL-998877"))
    assert result["status"] == "success"
    assert result["document_type"] == "health_insurance_card"
    assert result["extracted_fields"]["policy_number"]["value"] == "POL-998877"


def test_unknown_document_handling(service):
    result = service._normalize_payload({
        "status": "success",
        "document_type": "unknown",
        "overall_confidence": 0.0,
        "extracted_fields": {},
    })
    assert result["status"] == "error"
    assert result["document_type"] == "unknown"
    assert result["extracted_fields"] == {}


def test_invalid_malformed_extraction_response(service):
    with pytest.raises(ValueError):
        service._normalize_payload({
            "status": "success",
            "document_type": "aadhaar",
            "overall_confidence": 0.8,
            "extracted_fields": "not-a-dict",
        })


def test_missing_fields_are_null_and_zero_confidence(service):
    payload = {
        "status": "success",
        "document_type": "aadhaar",
        "overall_confidence": 0.91,
        "extracted_fields": {
            "full_name": {"value": "Muthu", "confidence": 0.95},
            "date_of_birth": None,
        },
    }
    result = service._normalize_payload(payload)
    assert result["extracted_fields"]["full_name"]["value"] == "Muthu"
    assert result["extracted_fields"]["date_of_birth"]["value"] is None
    assert result["extracted_fields"]["date_of_birth"]["confidence"] == 0.0


def test_field_level_and_overall_confidence(service):
    result = service._normalize_payload({
        "status": "success",
        "document_type": "pan_card",
        "overall_confidence": 0.87,
        "extracted_fields": {
            "full_name": {"value": "Asha K", "confidence": 0.92},
            "father_name": {"value": "Kumar", "confidence": 0.78},
            "date_of_birth": {"value": "04/05/1990", "confidence": 0.88},
            "pan_number": {"value": "ABCDE1234F", "confidence": 0.97},
        },
    })
    assert result["overall_confidence"] == 0.87
    assert result["extracted_fields"]["pan_number"]["confidence"] == 0.97
    assert result["extracted_fields"]["father_name"]["confidence"] == 0.78


def test_patient_profile_update_encrypts_and_tokens_identifiers():
    fields = {
        "full_name": {"value": "Ananya Sharma", "confidence": 0.99},
        "date_of_birth": {"value": "12/06/1999", "confidence": 0.98},
        "address": {"value": "24 Main Street", "confidence": 0.93},
        "father_name": {"value": "Ravi Sharma", "confidence": 0.9},
        "place_of_birth": {"value": "Chennai", "confidence": 0.92},
        "gender": {"value": "FEMALE", "confidence": 0.99},
        "aadhaar_number": {"value": "123456789012", "confidence": 0.98},
        "pan_number": {"value": "ABCDE1234F", "confidence": 0.99},
        "epic_number": {"value": "ZBC3635570", "confidence": 0.98},
        "driving_licence_number": {"value": "DL123456", "confidence": 0.97},
        "passport_number": {"value": "P1234567", "confidence": 0.96},
        "registration_number": {"value": "BR-1001", "confidence": 0.95},
        "member_id": {"value": "MEM-7788", "confidence": 0.94},
    }

    result = build_profile_update(fields, SimpleNamespace(id=ObjectId()))

    assert isinstance(result["name_enc"], Binary)
    assert isinstance(result["dob_enc"], Binary)
    assert isinstance(result["address_enc"], Binary)
    assert isinstance(result["guardian_name_enc"], Binary)
    assert isinstance(result["place_of_birth_enc"], Binary)
    assert isinstance(result["aadhaar_enc"], Binary)
    assert isinstance(result["pan_enc"], Binary)
    assert isinstance(result["voter_id_enc"], Binary)
    assert isinstance(result["driving_licence_enc"], Binary)
    assert isinstance(result["passport_enc"], Binary)
    assert isinstance(result["birth_reg_enc"], Binary)
    assert isinstance(result["health_insurance_enc"], Binary)
    assert result["aadhaar_token"]
    assert result["pan_token"]
    assert result["voter_id_token"]
    assert result["driving_licence_token"]
    assert result["passport_token"]
    assert result["birth_reg_token"]
    assert result["health_insurance_token"]
    assert result["gender"] == "FEMALE"


def test_source_document_redaction_hides_plaintext_sensitive_identifiers():
    payload = {
        "document_type": "aadhaar",
        "overall_confidence": 0.97,
        "extracted_fields": {
            "full_name": {"value": "Ananya Sharma", "confidence": 0.99},
            "aadhaar_number": {"value": "123456789012", "confidence": 0.98},
            "address": {"value": "24 Main Street", "confidence": 0.93},
        },
    }

    sanitized = redact_sensitive_extraction(payload)

    assert sanitized["extracted_fields"]["full_name"]["value"] == "Ananya Sharma"
    assert sanitized["extracted_fields"]["aadhaar_number"]["value"] is None
    assert sanitized["extracted_fields"]["address"]["value"] == "24 Main Street"


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("Male", "MALE"),
        ("male", "MALE"),
        ("M", "MALE"),
        ("Female", "FEMALE"),
        ("female", "FEMALE"),
        ("F", "FEMALE"),
        ("Other", "OTHER"),
        ("other", "OTHER"),
        ("Not specified", "Not specified"),
    ],
)
def test_gender_values_are_normalized_for_patient_profile(raw_value, expected):
    fields = {"gender": {"value": raw_value, "confidence": 0.99}}
    result = build_profile_update(fields, SimpleNamespace(id=ObjectId()))
    assert result["gender"] == expected


def test_missing_gender_value_does_not_update_profile():
    fields = {"gender": {"value": None, "confidence": 0.0}}
    result = build_profile_update(fields, SimpleNamespace(id=ObjectId()))
    assert "gender" not in result


def test_register_and_login_user_flow(monkeypatch):
    class FakeCollection:
        def __init__(self):
            self.rows = []

        def find_one(self, query, *args, **kwargs):
            if "phone_hash" in query:
                for row in self.rows:
                    if row.get("phone_hash") == query["phone_hash"]:
                        return row
            return None

        def insert_one(self, row):
            if "_id" not in row:
                row["_id"] = ObjectId()
            self.rows.append(row)
            return SimpleNamespace(inserted_id=row["_id"])

        def update_one(self, *args, **kwargs):
            return None

    class FakeDB:
        def __init__(self):
            self.users = FakeCollection()

    fake_db = FakeDB()
    monkeypatch.setattr("backend.services.auth_service.get_database", lambda: fake_db)
    monkeypatch.setattr("backend.services.auth_service.get_settings", lambda: SimpleNamespace(jwt_secret_key="12345678901234567890123456789012", jwt_algorithm="HS256"))
    monkeypatch.setattr("backend.auth.get_settings", lambda: SimpleNamespace(jwt_secret_key="12345678901234567890123456789012", jwt_algorithm="HS256"))

    user_id = register_user("+919876543210", "some-password", True)
    assert user_id is not None
    inserted_user = fake_db.users.rows[0]
    assert inserted_user["phone_hash"]
    assert isinstance(inserted_user["phone_enc"], Binary)
    assert "email_hash" not in inserted_user

    token = login_user("+919876543210", "some-password")
    assert token
    assert create_access_token(str(user_id))

    request = Request({"type": "http", "headers": [(b"authorization", f"Bearer {token}".encode())]})
    credentials = asyncio.run(security(request))
    auth_user_id = asyncio.run(get_authenticated_user_id(request, credentials))
    assert str(auth_user_id) == str(user_id)


def test_auth_routes_are_exposed():
    client = TestClient(app)
    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    paths = schema.json()["paths"]
    assert "/api/auth/register" in paths
    assert "/api/auth/login" in paths
    assert "/api/documents/extract" in paths
