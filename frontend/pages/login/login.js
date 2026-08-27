// frontend/pages/login/login.js

document.addEventListener("DOMContentLoaded", () => {
    redirectIfAuthenticated();

    const form = document.getElementById("loginForm");
    const phoneInput = document.getElementById("phone");
    const passwordInput = document.getElementById("password");

    const phoneError = document.getElementById("phoneError");
    const passwordError = document.getElementById("passwordError");
    const formError = document.getElementById("formError");

    const loginButton = document.getElementById("loginButton");
    const loginButtonText = document.getElementById("loginButtonText");
    const loginSpinner = document.getElementById("loginSpinner");

    const showPasswordButton = document.getElementById("showPassword");

    function clearErrors() {
        phoneError.textContent = "";
        passwordError.textContent = "";
        formError.textContent = "";

        phoneInput.classList.remove("invalid");
        passwordInput.classList.remove("invalid");
    }

    function validate() {
        let valid = true;

        const phone = phoneInput.value.trim();
        const password = passwordInput.value;

        if (!phone) {
            phoneError.textContent = "Phone number is required.";
            phoneInput.classList.add("invalid");
            valid = false;
        }

        if (!password) {
            passwordError.textContent = "Password is required.";
            passwordInput.classList.add("invalid");
            valid = false;
        }

        return valid;
    }

    function setLoading(loading) {
        loginButton.disabled = loading;
        loginButtonText.textContent = loading ? "Signing in..." : "Sign in";
        loginSpinner.hidden = !loading;
    }

    showPasswordButton.addEventListener("click", () => {
        const isPassword =
            passwordInput.type === "password";

        passwordInput.type =
            isPassword ? "text" : "password";

        showPasswordButton.textContent =
            isPassword ? "Hide" : "Show";
    });

    phoneInput.addEventListener("input", clearErrors);
    passwordInput.addEventListener("input", clearErrors);

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        clearErrors();

        if (!validate()) {
            return;
        }

        setLoading(true);

        try {
            const data = await apiRequest("/api/auth/login", {
                method: "POST",
                body: JSON.stringify({
                    phone: phoneInput.value.trim(),
                    password: passwordInput.value
                })
            });

            if (!data.access_token) {
                throw new Error(
                    "Login succeeded, but no access token was returned."
                );
            }

            saveAccessToken(data.access_token);

            window.location.href =
                "../dashboard/dashboard.html";

        } catch (error) {
            formError.textContent =
                error.message || "Unable to sign in.";

        } finally {
            setLoading(false);
        }
    });
});
