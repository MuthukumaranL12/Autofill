# MedForm Secure Database Layer

Zero-Trust MongoDB database engine designed for medical & government form autofill.
Compliant with DPDP Act 2023 & UIDAI Aadhaar storage regulations.

## Quick Setup Instructions

1. **Prerequisites:**
   - Install [MongoDB Community Server](https://www.mongodb.com/try/download/community).
   - Install VS Code with the **MongoDB for VS Code** extension.

2. **Run Database Initialization:**
   - Open VS Code and connect to `mongodb://localhost:27017`.
   - Open `scripts/setup_medform.mongodb.js`.
   - Click the **Play / Run** icon (or press `Ctrl+Alt+S`).

3. **Verify the Setup:**
   - Open `scripts/test_manual_pipeline.mongodb.js` and click **Run**.
   - All tests should return `✔ PASS`.