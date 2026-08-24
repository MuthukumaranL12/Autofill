from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.document_extraction.gemini_service import GeminiExtractionService


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
