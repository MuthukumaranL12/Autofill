// frontend/pages/profile/profile.js

document.addEventListener("DOMContentLoaded", () => {
    requireAuthentication();

    const form = document.getElementById("profileForm");
    const loadingState = document.getElementById("loadingState");
    const emptyState = document.getElementById("emptyState");
    const pageMessage = document.getElementById("pageMessage");

    const saveButton = document.getElementById("saveButton");
    const saveButtonText =
        document.getElementById("saveButtonText");
    const saveSpinner =
        document.getElementById("saveSpinner");

    const cancelButton =
        document.getElementById("cancelButton");

    const saveStatus =
        document.getElementById("saveStatus");

    const fields = [
        "name",
        "first_name",
        "middle_name",
        "last_name",
        "dob",
        "address",
        "house_number",
        "street",
        "locality",
        "city",
        "state",
        "pincode",
        "guardian_name",
        "place_of_birth",
        "gender",
        "year_of_birth",
        "aadhaar_number",
        "voter_id",
        "birth_registration_number",
    ];

    let originalProfile = null;

    function setPageError(message) {
        pageMessage.textContent = message || "";
    }

    function getFormData() {
        const data = {};

        fields.forEach((fieldName) => {
            const element =
                document.getElementById(fieldName);

            data[fieldName] = element.value;
        });

        return data;
    }

    function fillForm(profile) {
        fields.forEach((fieldName) => {
            const element =
                document.getElementById(fieldName);

            if (!element) {
                return;
            }

            element.value =
                profile[fieldName] ?? "";
        });
    }

    function setLoading(loading) {
        saveButton.disabled = loading;

        saveButtonText.textContent =
            loading
                ? "Saving..."
                : "Save changes";

        saveSpinner.hidden = !loading;
    }

    async function loadProfile() {
        setPageError("");

        try {
            const profile =
                await apiRequest("/api/profile/", {
                    method: "GET"
                });

            originalProfile = {
                ...profile
            };

            fillForm(profile);

            loadingState.hidden = true;
            emptyState.hidden = true;
            form.hidden = false;

        } catch (error) {
            loadingState.hidden = true;

            if (
                error.message &&
                error.message.toLowerCase().includes(
                    "profile not found"
                )
            ) {
                emptyState.hidden = false;
                form.hidden = true;
                return;
            }

            setPageError(
                error.message ||
                "Unable to load your profile."
            );

            emptyState.hidden = false;
            form.hidden = true;
        }
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        setPageError("");
        saveStatus.textContent = "";

        const profileData = getFormData();

        setLoading(true);

        try {
            const updated =
                await apiRequest("/api/profile/", {
                    method: "PUT",
                    body: JSON.stringify(profileData)
                });

            originalProfile = {
                ...updated
            };

            fillForm(updated);

            saveStatus.textContent =
                "Changes saved successfully.";

        } catch (error) {
            setPageError(
                error.message ||
                "Unable to save your profile."
            );

        } finally {
            setLoading(false);
        }
    });

    cancelButton.addEventListener("click", () => {
        if (!originalProfile) {
            return;
        }

        fillForm(originalProfile);

        setPageError("");

        saveStatus.textContent =
            "Changes reset.";
    });

    loadProfile();
});
