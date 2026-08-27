// frontend/pages/upload/upload.js

document.addEventListener("DOMContentLoaded", () => {
    console.log("[MedForm] upload.js loaded");

    // Authentication
    if (typeof requireAuthentication === "function") {
        requireAuthentication();
    }

    const fileInput = document.getElementById("documentFile");
    const uploadArea = document.getElementById("uploadArea");
    const selectedFile = document.getElementById("selectedFile");
    const fileName = document.getElementById("fileName");
    const fileSize = document.getElementById("fileSize");
    const fileIcon = document.getElementById("fileIcon");
    const removeButton = document.getElementById("removeButton");

    const extractButton = document.getElementById("extractButton");
    const extractButtonText =
        document.getElementById("extractButtonText");
    const extractSpinner =
        document.getElementById("extractSpinner");

    const uploadState = document.getElementById("uploadState");
    const processingState =
        document.getElementById("processingState");
    const savedState = document.getElementById("savedState");

    const uploadError = document.getElementById("uploadError");

    const consentModal =
        document.getElementById("consentModal");
    const consentFields =
        document.getElementById("consentFields");
    const consentCheckbox =
        document.getElementById("consentCheckbox");
    const consentError =
        document.getElementById("consentError");

    const acceptConsentButton =
        document.getElementById("acceptConsentButton");
    const declineConsentButton =
        document.getElementById("declineConsentButton");

    const stepUpload =
        document.getElementById("stepUpload");
    const stepReview =
        document.getElementById("stepReview");
    const stepSaved =
        document.getElementById("stepSaved");

    const uploadAnotherButton =
        document.getElementById("uploadAnotherButton");

    let selectedFileObject = null;
    let extractedData = null;

    const MAX_SIZE = 10 * 1024 * 1024;
    const ALLOWED_EXTENSIONS = [
        "pdf",
        "jpg",
        "jpeg",
        "png"
    ];

    // ---------------------------------------------------------
    // BASIC VALIDATION
    // ---------------------------------------------------------

    function validateFile(file) {
        if (!file) {
            return "Please select a document.";
        }

        const extension = file.name
            .split(".")
            .pop()
            .toLowerCase();

        if (!ALLOWED_EXTENSIONS.includes(extension)) {
            return (
                "Only PDF, JPG, JPEG and PNG files are allowed."
            );
        }

        if (file.size > MAX_SIZE) {
            return "The document must be smaller than 10 MB.";
        }

        return null;
    }

    function showError(message) {
        uploadError.textContent = message || "";
        uploadError.hidden = !message;
    }

    function clearError() {
        showError("");
        consentError.textContent = "";
    }

    function formatSize(bytes) {
        if (bytes < 1024) {
            return `${bytes} B`;
        }

        if (bytes < 1024 * 1024) {
            return `${(bytes / 1024).toFixed(1)} KB`;
        }

        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    // ---------------------------------------------------------
    // STEPS
    // ---------------------------------------------------------

    function setStep(stage) {
        stepUpload.classList.remove(
            "active",
            "complete"
        );

        stepReview.classList.remove(
            "active",
            "complete"
        );

        stepSaved.classList.remove(
            "active",
            "complete"
        );

        if (stage === "upload") {
            stepUpload.classList.add("active");
        }

        if (stage === "review") {
            stepUpload.classList.add("complete");
            stepReview.classList.add("active");
        }

        if (stage === "saved") {
            stepUpload.classList.add("complete");
            stepReview.classList.add("complete");
            stepSaved.classList.add("active");
        }
    }

    // ---------------------------------------------------------
    // FILE SELECTION
    // ---------------------------------------------------------

    function selectFile(file) {
        clearError();

        const error = validateFile(file);

        if (error) {
            selectedFileObject = null;
            selectedFile.hidden = true;
            extractButton.disabled = true;
            showError(error);
            return;
        }

        selectedFileObject = file;

        fileName.textContent = file.name;
        fileSize.textContent = formatSize(file.size);
        fileIcon.textContent =
            file.name.split(".").pop().toUpperCase();

        selectedFile.hidden = false;
        extractButton.disabled = false;

        console.log(
            "[MedForm] file selected:",
            file.name
        );
    }

    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];

        if (file) {
            selectFile(file);
        }
    });

    removeButton.addEventListener("click", () => {
        fileInput.value = "";
        selectedFileObject = null;
        extractedData = null;

        selectedFile.hidden = true;
        extractButton.disabled = true;

        clearError();
    });

    // ---------------------------------------------------------
    // DRAG & DROP
    // ---------------------------------------------------------

    uploadArea.addEventListener("dragover", (event) => {
        event.preventDefault();
        uploadArea.classList.add("drag-over");
    });

    uploadArea.addEventListener("dragleave", () => {
        uploadArea.classList.remove("drag-over");
    });

    uploadArea.addEventListener("drop", (event) => {
        event.preventDefault();
        uploadArea.classList.remove("drag-over");

        const file = event.dataTransfer.files[0];

        if (file) {
            selectFile(file);
        }
    });

    // ---------------------------------------------------------
    // EXTRACT BUTTON
    // ---------------------------------------------------------

    extractButton.addEventListener(
        "click",
        async () => {
            console.log(
                "[MedForm] Extract button clicked"
            );

            clearError();

            if (!selectedFileObject) {
                showError(
                    "Please select a document first."
                );
                return;
            }

            extractButton.disabled = true;
            extractButtonText.textContent =
                "Extracting...";
            extractSpinner.hidden = false;

            uploadState.hidden = true;
            processingState.hidden = false;

            setStep("upload");

            try {
                const formData = new FormData();

                formData.append(
                    "file",
                    selectedFileObject
                );

                console.log(
                    "[MedForm] calling /api/documents/extract"
                );

                if (typeof apiRequest !== "function") {
                    throw new Error(
                        "apiRequest is not available. " +
                        "Check ../../js/api.js"
                    );
                }

                const response = await apiRequest(
                    "/api/documents/extract",
                    {
                        method: "POST",
                        body: formData
                    }
                );

                console.log(
                    "[MedForm] extraction response received:",
                    response
                );

                /*
                 * IMPORTANT:
                 * Keep the original Gemini ExtractionResponse
                 * in browser memory.
                 *
                 * Nothing is saved here.
                 */
                extractedData = response;

                processingState.hidden = true;

                extractButtonText.textContent =
                    "Extract information";
                extractSpinner.hidden = true;

                openConsentModal();

            } catch (error) {
                console.error(
                    "[MedForm] extraction failed:",
                    error
                );

                processingState.hidden = true;
                uploadState.hidden = false;

                extractButton.disabled = false;
                extractButtonText.textContent =
                    "Extract information";
                extractSpinner.hidden = true;

                showError(
                    error?.message ||
                    "Unable to extract information."
                );
            }
        }
    );

    // ---------------------------------------------------------
    // HELPERS FOR CONSENT DISPLAY
    // ---------------------------------------------------------

    function escapeHtml(value) {
        const element =
            document.createElement("div");

        element.textContent =
            String(value ?? "");

        return element.innerHTML;
    }

    function labelFor(key) {
        return String(key)
            .replace(/_/g, " ")
            .replace(
                /\b\w/g,
                (char) => char.toUpperCase()
            );
    }

    function formatDocumentType(value) {
        return String(value)
            .replace(/_/g, " ")
            .replace(
                /\b\w/g,
                (char) => char.toUpperCase()
            );
    }

    function getDisplayValue(fieldData) {
        if (
            fieldData &&
            typeof fieldData === "object" &&
            Object.prototype.hasOwnProperty.call(
                fieldData,
                "value"
            )
        ) {
            return fieldData.value;
        }

        return fieldData;
    }

    // ---------------------------------------------------------
    // CONSENT MODAL
    // ---------------------------------------------------------

    function openConsentModal() {
        console.log(
            "[MedForm] OPENING CONSENT MODAL"
        );

        consentFields.innerHTML = "";
        consentError.textContent = "";

        consentCheckbox.checked = false;
        acceptConsentButton.disabled = true;

        if (
            !extractedData ||
            typeof extractedData !== "object"
        ) {
            consentFields.innerHTML = `
                <div class="consent-empty">
                    No extracted information is available.
                </div>
            `;

            setStep("review");

            consentModal.hidden = false;
            document.body.classList.add(
                "modal-open"
            );

            return;
        }

        /*
         * Real Gemini response:
         *
         * {
         *   status: "success",
         *   document_type: "aadhaar",
         *   overall_confidence: 0.92,
         *   extracted_fields: {
         *      full_name: {
         *          value: "...",
         *          confidence: 0.98
         *      }
         *   }
         * }
         */

        const documentType =
            extractedData.document_type;

        if (documentType) {
            const row =
                document.createElement("div");

            row.className = "consent-field";

            row.innerHTML = `
                <label>Document Type</label>
                <span>
                    ${escapeHtml(
                        formatDocumentType(
                            documentType
                        )
                    )}
                </span>
            `;

            consentFields.appendChild(row);
        }

        const fields =
            extractedData.extracted_fields || {};

        const entries =
            Object.entries(fields).filter(
                ([, fieldData]) => {
                    const value =
                        getDisplayValue(fieldData);

                    return (
                        value !== null &&
                        value !== undefined &&
                        value !== ""
                    );
                }
            );

        if (entries.length === 0) {
            const empty =
                document.createElement("div");

            empty.className = "consent-empty";
            empty.textContent =
                "No readable identity information was extracted.";

            consentFields.appendChild(empty);
        } else {
            entries.forEach(
                ([key, fieldData]) => {
                    const value =
                        getDisplayValue(fieldData);

                    const row =
                        document.createElement("div");

                    row.className =
                        "consent-field";

                    row.innerHTML = `
                        <label>
                            ${escapeHtml(
                                labelFor(key)
                            )}
                        </label>

                        <span>
                            ${escapeHtml(value)}
                        </span>
                    `;

                    consentFields.appendChild(row);
                }
            );
        }

        /*
         * Display confidence for the user only.
         * The original extraction object remains untouched
         * and is sent to /consent.
         */
        if (
            typeof extractedData.overall_confidence
                === "number"
        ) {
            const confidence =
                document.createElement("div");

            confidence.className =
                "consent-field";

            confidence.innerHTML = `
                <label>Extraction Confidence</label>
                <span>
                    ${Math.round(
                        extractedData
                            .overall_confidence * 100
                    )}%
                </span>
            `;

            consentFields.appendChild(
                confidence
            );
        }

        setStep("review");

        /*
         * Show modal only after extraction succeeded.
         */
        consentModal.hidden = false;

        document.body.classList.add(
            "modal-open"
        );

        console.log(
            "[MedForm] consentModal.hidden =",
            consentModal.hidden
        );
    }

    function closeConsentModal() {
        consentModal.hidden = true;

        document.body.classList.remove(
            "modal-open"
        );
    }

    consentCheckbox.addEventListener(
        "change",
        () => {
            acceptConsentButton.disabled =
                !consentCheckbox.checked;
        }
    );

    // ---------------------------------------------------------
    // DECLINE
    // ---------------------------------------------------------

    declineConsentButton.addEventListener(
        "click",
        () => {
            console.log(
                "[MedForm] user declined consent"
            );

            /*
             * Discard extracted information from memory.
             * No request is made to the backend.
             */
            extractedData = null;

            closeConsentModal();

            uploadState.hidden = false;
            processingState.hidden = true;
            savedState.hidden = true;

            extractButton.disabled =
                !selectedFileObject;

            extractButtonText.textContent =
                "Extract information";

            extractSpinner.hidden = true;

            setStep("upload");
        }
    );

    // ---------------------------------------------------------
    // ACCEPT / SAVE
    // ---------------------------------------------------------

    acceptConsentButton.addEventListener(
        "click",
        async () => {
            if (!consentCheckbox.checked) {
                return;
            }

            if (!extractedData) {
                consentError.textContent =
                    "No extracted information is available. Please upload again.";
                return;
            }

            acceptConsentButton.disabled = true;
            declineConsentButton.disabled = true;

            acceptConsentButton.textContent =
                "Saving...";

            consentError.textContent = "";

            try {
                console.log(
                    "[MedForm] sending POST /api/documents/consent"
                );

                /*
                 * Send the ORIGINAL Gemini extraction
                 * response. The backend converts it into
                 * the persistence format.
                 */
                const result = await apiRequest(
                    "/api/documents/consent",
                    {
                        method: "POST",
                        body: JSON.stringify({
                            consent_given: true,
                            extraction: extractedData
                        })
                    }
                );

                console.log(
                    "[MedForm] consent save response:",
                    result
                );

                extractedData = null;

                closeConsentModal();

                uploadState.hidden = true;
                processingState.hidden = true;
                savedState.hidden = false;

                setStep("saved");

            } catch (error) {
                console.error(
                    "[MedForm] consent save failed:",
                    error
                );

                consentError.textContent =
                    error?.message ||
                    "Unable to save the approved information.";

                acceptConsentButton.disabled = false;
                declineConsentButton.disabled = false;

                acceptConsentButton.textContent =
                    "I Consent & Save";
            }
        }
    );

    // ---------------------------------------------------------
    // CLICK OUTSIDE MODAL = DECLINE
    // ---------------------------------------------------------

    consentModal.addEventListener(
        "click",
        (event) => {
            if (
                event.target === consentModal
            ) {
                extractedData = null;

                closeConsentModal();

                uploadState.hidden = false;
                processingState.hidden = true;

                extractButton.disabled =
                    !selectedFileObject;

                extractButtonText.textContent =
                    "Extract information";

                extractSpinner.hidden = true;

                setStep("upload");
            }
        }
    );

    // ---------------------------------------------------------
    // UPLOAD ANOTHER
    // ---------------------------------------------------------

    uploadAnotherButton.addEventListener(
        "click",
        () => {
            fileInput.value = "";

            selectedFileObject = null;
            extractedData = null;

            selectedFile.hidden = true;

            extractButton.disabled = true;

            extractButtonText.textContent =
                "Extract information";

            extractSpinner.hidden = true;

            savedState.hidden = true;
            processingState.hidden = true;
            uploadState.hidden = false;

            setStep("upload");
            clearError();
        }
    );

    // ---------------------------------------------------------
    // INITIAL STATE
    // ---------------------------------------------------------

    uploadState.hidden = false;
    processingState.hidden = true;
    savedState.hidden = true;
    consentModal.hidden = true;

    console.log(
        "[MedForm] upload page initialized"
    );
});
