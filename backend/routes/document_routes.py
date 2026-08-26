from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.auth import get_authenticated_user_id
from backend.services.document_service import persist_extraction
from backend.dependencies import get_extraction_service
from backend.document_extraction.gemini_service import GeminiExtractionService
from backend.document_extraction.schemas import ExtractionResponse
from backend.settings import get_settings

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
    file: UploadFile = File(...),
    service: GeminiExtractionService = Depends(get_extraction_service),
    user_id=Depends(get_authenticated_user_id),
) -> ExtractionResponse:
    filename = file.filename or "document"
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix or 'unknown'}. Allowed: pdf, jpg, jpeg, png",
        )

    temp_dir = get_settings().upload_dir
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{uuid4().hex}{suffix}"

    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        temp_path.write_bytes(contents)
        result = service.extract_document(temp_path, ALLOWED_EXTENSIONS[suffix])
        persist_extraction(user_id, result.model_dump(mode="python"))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
