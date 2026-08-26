from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
import os
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from backend.document_extraction.extraction import parse_json_response
from backend.document_extraction.schemas import ExtractionResponse


DOCUMENT_TYPE_ALIASES: dict[str, str] = {
    "aadhaar": "aadhaar",
    "aadhaar card": "aadhaar",
    "aadhar": "aadhaar",
    "aadhar card": "aadhaar",
    "pan": "pan_card",
    "pan_card": "pan_card",
    "pan card": "pan_card",
    "permanent account number card": "pan_card",
    "passport": "passport",
    "driving_licence": "driving_licence",
    "driving licence": "driving_licence",
    "driving license": "driving_licence",
    "driving licence card": "driving_licence",
    "driving license card": "driving_licence",
    "voter_id": "voter_id",
    "voter id": "voter_id",
    "voter id card": "voter_id",
    "voter identification card": "voter_id",
    "birth_certificate": "birth_certificate",
    "birth certificate": "birth_certificate",
    "health_insurance_card": "health_insurance_card",
    "health insurance card": "health_insurance_card",
    "insurance card": "health_insurance_card",
}

DOCUMENT_FIELD_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "aadhaar": (
        "full_name", "date_of_birth", "gender", "aadhaar_number", "address",
        "year_of_birth", "mobile_number", "father_or_husband_name",
    ),
    "pan_card": ("full_name", "father_name", "date_of_birth", "pan_number"),
    "passport": (
        "full_name", "surname", "given_names", "passport_number", "nationality",
        "date_of_birth", "gender", "place_of_birth", "place_of_issue",
        "date_of_issue", "date_of_expiry", "father_name", "mother_name",
        "spouse_name", "address", "file_number", "personal_number",
    ),
    "driving_licence": (
        "full_name", "date_of_birth", "gender", "driving_licence_number",
        "address", "date_of_issue", "validity_from", "validity_to",
        "issuing_authority", "vehicle_classes", "blood_group",
        "father_or_husband_name",
    ),
    "voter_id": (
        "full_name", "relative_name", "relationship_type", "date_of_birth",
        "age", "gender", "epic_number", "address", "constituency",
        "polling_station", "part_number", "serial_number", "issuing_authority",
    ),
    "birth_certificate": (
        "child_full_name", "date_of_birth", "time_of_birth", "gender",
        "place_of_birth", "father_name", "mother_name", "father_nationality",
        "mother_nationality", "father_address", "mother_address",
        "registration_number", "registration_date", "date_of_registration",
        "issuing_authority", "registration_unit",
    ),
    "health_insurance_card": (
        "patient_name", "member_name", "member_id", "policy_number", "insurance_id",
        "group_number", "insurer_name", "insurance_company", "plan_name",
        "policy_holder_name", "relationship_to_policy_holder", "date_of_birth",
        "gender", "policy_start_date", "policy_end_date", "validity", "customer_id",
        "card_number", "claim_number", "tpa_name", "tpa_id", "network_name",
        "helpline_number", "address",
    ),
}

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "full_name": ("full_name", "name"),
    "date_of_birth": ("date_of_birth", "dob", "birth_date"),
    "aadhaar_number": ("aadhaar_number", "aadhaar_no", "aadhaar number"),
    "pan_number": ("pan_number", "pan_no", "pan number"),
    "driving_licence_number": ("driving_licence_number", "driving_license_number", "dl_no"),
    "father_or_husband_name": ("father_or_husband_name", "father_name", "husband_name"),
    "date_of_issue": ("date_of_issue", "issue_date"),
    "date_of_expiry": ("date_of_expiry", "expiry_date"),
    "epic_number": ("epic_number", "voter_id_number", "epic_no"),
    "insurance_company": ("insurance_company", "insurance_provider", "insurer_name"),
    "member_id": ("member_id", "insurance_member_id"),
    "policy_number": ("policy_number", "insurance_policy_number", "policy_no"),
}

DOCUMENT_EXTRACTION_PROMPT = """
You are an expert document information extraction system.

Analyze the uploaded document carefully.

Determine the document type. It must be exactly one of:
aadhaar, pan_card, passport, driving_licence, voter_id, birth_certificate,
health_insurance_card, or unknown.

For aadhaar extract only: full_name, date_of_birth, gender, aadhaar_number,
address, year_of_birth, mobile_number, father_or_husband_name.
For pan_card extract only: full_name, father_name, date_of_birth, pan_number.
For passport extract only: full_name, surname, given_names, passport_number,
nationality, date_of_birth, gender, place_of_birth, place_of_issue, date_of_issue,
date_of_expiry, father_name, mother_name, spouse_name, address, file_number,
personal_number.
For driving_licence extract only: full_name, date_of_birth, gender,
driving_licence_number, address, date_of_issue, validity_from, validity_to,
issuing_authority, vehicle_classes, blood_group, father_or_husband_name.
For voter_id, extract only these fields:
full_name, relative_name, relationship_type, date_of_birth, age,
gender, epic_number, address, constituency, polling_station,
part_number, serial_number, issuing_authority.
For epic_number:
- Carefully inspect the entire voter ID image for the EPIC/Voter ID number.
- Extract the exact alphanumeric value as printed on the card.
- Do not return null if the EPIC number is clearly visible anywhere on the document.
- Preserve the characters exactly as printed.
- Do not confuse the EPIC number with part number, serial number, Aadhaar number, or other numbers.
- Return null only when the EPIC number is genuinely absent, unreadable, or not visible.
For birth_certificate extract only: child_full_name, date_of_birth, time_of_birth,
gender, place_of_birth, father_name, mother_name, father_nationality,
mother_nationality, father_address, mother_address, registration_number,
registration_date, date_of_registration, issuing_authority, registration_unit.
For health_insurance_card extract only: patient_name, member_name, member_id,
policy_number, insurance_id, group_number, insurer_name, insurance_company,
plan_name, policy_holder_name, relationship_to_policy_holder, date_of_birth,
gender, policy_start_date, policy_end_date, validity, customer_id, card_number,
claim_number, tpa_name, tpa_id, network_name, helpline_number, address.

Use the exact canonical field names above. Every extracted field must be an object
with a value and a confidence between 0 and 1. Use null and confidence 0 for
fields that are missing, unreadable, or not present. If the document cannot be
identified confidently, return unknown with an empty object.

Do not combine documents, infer values, correct spellings, or invent information.
Preserve dates, numbers, addresses, and names exactly as visible. For passport
MRZ data, cross-check it against visible fields and use null if it is unreliable.
Return ONLY valid JSON.

Rules:
- No markdown.
- No explanations.
- No code blocks.
- No additional text.
- Use null when information is missing.
- Preserve exact values from the document.
- Extract as many relevant fields as possible.

Output format:

{
    "status": "success",
    "document_type": "aadhaar",
    "overall_confidence": 0.0,
  "extracted_fields": {}
}
""".strip()


class GeminIConfig:
    def __init__(self, gemini_api_key: str, gemini_model: str, gemini_api_version: str, upload_dir: Path, results_dir: Path):
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model
        self.gemini_api_version = gemini_api_version
        self.upload_dir = upload_dir
        self.results_dir = results_dir


class GeminiExtractionService:
    _max_retries = 3

    def __init__(self, settings: Any) -> None:
        api_key = getattr(settings, "gemini_api_key", None) or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self._settings = settings
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version=getattr(settings, "gemini_api_version", "v1alpha")),
        )

    def extract_document(self, file_path: Path, mime_type: str) -> ExtractionResponse:
        try:
            document_bytes = file_path.read_bytes()
            document_part = types.Part.from_bytes(data=document_bytes, mime_type=mime_type)
            response = self._generate_content_with_retries(document_part)
        except errors.APIError as exc:
            raise RuntimeError(f"Gemini API request failed: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"Failed to process uploaded document: {exc}") from exc

        response_text = self._get_response_text(response)

        try:
            payload = parse_json_response(response_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Gemini returned invalid JSON: {exc}") from exc

        try:
            normalized_payload = self._normalize_payload(payload)
            return ExtractionResponse.model_validate(normalized_payload)
        except (TypeError, ValueError, ValidationError) as exc:
            raise ValueError(f"Gemini response did not match the expected extraction structure: {exc}") from exc

    @staticmethod
    def _get_response_text(response: Any) -> str:
        response_text = getattr(response, "text", None)
        if response_text:
            return response_text

        candidates = getattr(response, "candidates", None) or []
        parts: list[str] = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if content is None:
                continue
            for part in getattr(content, "parts", []) or []:
                text = getattr(part, "text", None)
                if text:
                    parts.append(text)

        if parts:
            return "".join(parts)

        raise ValueError("Gemini response did not contain any text")

    def _generate_content_with_retries(self, document_part: types.Part) -> Any:
        last_error: errors.APIError | None = None

        for attempt in range(self._max_retries):
            try:
                return self._client.models.generate_content(
                    model=getattr(self._settings, "gemini_model", "gemini-2.5-flash"),
                    contents=[document_part],
                    config=types.GenerateContentConfig(
                        system_instruction=DOCUMENT_EXTRACTION_PROMPT,
                        temperature=0,
                        top_p=1,
                        max_output_tokens=4096,
                        response_mime_type="application/json",
                    ),
                )
            except errors.APIError as exc:
                last_error = exc
                if not self._is_transient_api_error(exc) or attempt >= self._max_retries - 1:
                    raise
                time.sleep(2 ** attempt)

        if last_error is not None:
            raise last_error

        raise RuntimeError("Gemini API request failed for an unknown reason")

    @staticmethod
    def _is_transient_api_error(exc: errors.APIError) -> bool:
        code = getattr(exc, "code", None)
        if code in {429, 500, 502, 503, 504}:
            return True

        message = str(exc).lower()
        return any(keyword in message for keyword in ("unavailable", "temporarily", "high demand", "timeout"))

    def _normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("Gemini response must be a JSON object")

        raw_document_type = str(payload.get("document_type", "")).strip()
        normalized_document_type = self._normalize_document_type(raw_document_type)
        extracted_fields = payload.get("extracted_fields") or {}
        if not isinstance(extracted_fields, dict):
            raise ValueError("extracted_fields must be a JSON object")

        if normalized_document_type == "unknown":
            return {
                "status": "error",
                "document_type": "unknown",
                "overall_confidence": 0.0,
                "extracted_fields": {},
                "error": "Unable to identify the document type",
            }

        allowlist = DOCUMENT_FIELD_ALLOWLIST.get(normalized_document_type)
        if allowlist is None:
            return {
                "status": "error",
                "document_type": "unknown",
                "overall_confidence": 0.0,
                "extracted_fields": {},
                "error": "Unable to identify the document type",
            }

        filtered_fields = {
            field_name: self._field_result(extracted_fields, FIELD_ALIASES.get(field_name, (field_name,)))
            for field_name in allowlist
        }

        return {
            "status": "success",
            "document_type": normalized_document_type,
            "overall_confidence": float(payload.get("overall_confidence", payload.get("confidence_score", 0.0))),
            "extracted_fields": filtered_fields,
        }

    @staticmethod
    def _normalize_document_type(document_type: str) -> str:
        key = document_type.strip().lower()
        if not key:
            return "unknown"
        return DOCUMENT_TYPE_ALIASES.get(key, "unknown")

    @staticmethod
    def _field_result(extracted_fields: dict[str, Any], aliases: tuple[str, ...]) -> dict[str, Any]:
        normalized_fields = {str(key).strip().lower(): value for key, value in extracted_fields.items()}

        for alias in aliases:
            alias_key = alias.strip().lower()
            if alias_key in normalized_fields:
                value = normalized_fields[alias_key]
                if isinstance(value, dict):
                    return {
                        "value": value.get("value"),
                        "confidence": max(0.0, min(1.0, float(value.get("confidence", 0.0)))),
                    }
                return {"value": value, "confidence": 0.0}

        return {"value": None, "confidence": 0.0}
