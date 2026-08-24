from __future__ import annotations

from functools import lru_cache

from backend.document_extraction.gemini_service import GeminiExtractionService
from backend.settings import get_settings


@lru_cache(maxsize=1)
def get_extraction_service() -> GeminiExtractionService:
    return GeminiExtractionService(get_settings())
