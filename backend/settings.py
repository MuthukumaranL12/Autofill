from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = ROOT_DIR / "uploads" / "temp"
RESULTS_DIR = ROOT_DIR / "uploads" / "documents"


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_version: str = "v1alpha"
    max_upload_size_mb: int = 25
    upload_dir: Path = UPLOAD_DIR
    results_dir: Path = RESULTS_DIR


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set")

    settings = Settings(
        gemini_api_key=gemini_api_key,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
        gemini_api_version=os.getenv("GEMINI_API_VERSION", "v1alpha").strip(),
        max_upload_size_mb=int(os.getenv("MAX_UPLOAD_SIZE_MB", "25")),
    )

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.results_dir.mkdir(parents=True, exist_ok=True)
    return settings
