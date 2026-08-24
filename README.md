# Major Project Unified Backend

This repository contains a unified FastAPI project centered on the working document extraction service. The current implementation is the reusable Gemini-powered extraction module. The MongoDB, profile, form-filling, and frontend areas are intentionally kept as placeholders for future development.

## Current implemented component

- Document Extraction
- Gemini API integration
- Structured JSON response
- File validation for PDF, JPG, JPEG, and PNG

## Future placeholders

- MongoDB / database layer
- Profile features
- Form filling pipeline
- Frontend shell

## Run the backend

```bash
python -m uvicorn backend.app:app --reload
```

The application is available at `http://127.0.0.1:8000`.

## Extract document request

```bash
curl -X POST "http://127.0.0.1:8000/api/documents/extract" \
  -H "accept: application/json" \
  -F "file=@sample.pdf"
```

## Response shape

```json
{
  "status": "success",
  "document_type": "aadhaar",
  "overall_confidence": 0.99,
  "extracted_fields": {
    "full_name": {
      "value": "Muthukumaran L",
      "confidence": 0.99
    },
    "date_of_birth": {
      "value": "12/03/2005",
      "confidence": 0.98
    }
  }
}
```

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and add `GEMINI_API_KEY`.

## Notes

- The source of truth is the working document extraction component.
- The FastAPI app is a single server registered from `backend/app.py`.
- The database, form, and profile directories are intentionally minimal placeholders and do not contain live logic yet.
- No API keys or secrets are committed to the repository.