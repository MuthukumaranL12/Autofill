

# Consent-Based Intelligent Identity Autofill System

A privacy-focused identity document extraction and autofill system built with **FastAPI**, **Google Gemini**, and **MongoDB**. It extracts structured information from identity documents and supports consent-based profile storage and form filling.

## Features

- **Document Extraction:** Uses Google Gemini to identify identity documents and extract structured information from PDF, JPG, JPEG, and PNG files.
- **Structured Responses:** Normalizes extracted fields and validates the output using Pydantic schemas.
- **Confidence Scoring:** Provides field-level and overall confidence estimates for extracted information.
- **Consent-Based Storage:** Separates document extraction from saving information to a user's profile.
- **Profile Management:** Supports profile-related operations and sensitive information handling.
- **Form Autofill:** Includes a backend pipeline for processing form fields and autofill operations.
- **Authentication and Security:** Includes JWT-based authentication, refresh-token handling, encryption utilities, rate limiting, and security logging.

## Tech Stack

- **Backend:** Python, FastAPI
- **Document AI:** Google Gemini API
- **Database:** MongoDB
- **Validation:** Pydantic
- **Authentication:** JWT
- **Security:** Cryptography, bcrypt, HMAC
- **Frontend:** HTML, CSS, JavaScript
- **Testing:** Pytest

## Project Structure

```text
├── backend/
│   ├── database/
│   ├── document_extraction/
│   ├── form_pipeline/
│   ├── models/
│   ├── repositories/
│   ├── routes/
│   ├── security/
│   ├── services/
│   └── app.py
│
├── frontend/
├── forms/
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Setup and Run

### 1. Clone the repository

```bash
git clone <repository-url>
cd Autofill-main
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and configure the required values, including your Gemini API key and database credentials.

```env
GEMINI_API_KEY=your_gemini_api_key
MONGODB_URI=your_mongodb_connection_string
MONGODB_DATABASE=your_database_name
```

Add the required security secrets as specified in `.env.example`. Do not commit `.env` or expose secret values.

### 5. Start the application

```bash
python -m uvicorn backend.app:app --reload
```

The application will be available at:

- Application: `http://127.0.0.1:8000`
- API documentation: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## Document Extraction API

**Endpoint:** `POST /api/documents/extract`

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/api/documents/extract" \
  -H "accept: application/json" \
  -F "file=@sample.pdf"
```

Example response:

```json
{
  "status": "success",
  "document_type": "aadhaar",
  "overall_confidence": 0.99,
  "extracted_fields": {
    "full_name": {
      "value": "Example Name",
      "confidence": 0.99
    },
    "date_of_birth": {
      "value": "12/03/2005",
      "confidence": 0.98
    }
  }
}
```

The response is illustrative. Actual extracted fields and confidence values depend on the uploaded document.

## Run Tests

```bash
pytest
```

## Security and Privacy

The system is designed around consent-based handling of identity information. Extracted data is kept separate from profile storage until the user explicitly consents to saving it. Sensitive information is handled using the repository's encryption, masking, and authentication utilities.

---

**Note:** Gemini confidence scores are model-generated estimates and should not be interpreted as statistically calibrated accuracy measurements.

