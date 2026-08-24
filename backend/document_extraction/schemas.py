from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    value: Any | None = None
    confidence: float = Field(..., ge=0.0, le=1.0)


class ExtractionResponse(BaseModel):
    status: Literal["success", "error"]
    document_type: str = Field(..., min_length=1)
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    extracted_fields: dict[str, ExtractedField] = Field(default_factory=dict)
    error: str | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
