from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.document_extraction.gemini_service import GeminiExtractionService
from backend.document_extraction.schemas import ExtractionResponse


@dataclass
class DocumentExtractor:
    service: GeminiExtractionService

    def extract(self, file_path: str | Path, mime_type: str) -> ExtractionResponse:
        return self.service.extract_document(Path(file_path), mime_type)
