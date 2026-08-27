// frontend/pages/dashboard/dashboard.js

document.addEventListener("DOMContentLoaded", () => {
    requireAuthentication();

    const welcomeUser =
        document.getElementById("welcomeUser");

    const greeting =
        document.getElementById("greeting");

    const avatarButton =
        document.getElementById("avatarButton");

    const profileAvatar =
        document.getElementById("profileAvatar");

    const userMenu =
        document.getElementById("userMenu");

    const logoutButton =
        document.getElementById("logoutButton");

    const profileName =
        document.getElementById("profileName");

    /*
     * For now, authentication only returns the token.
     * Your current profile endpoint is still a placeholder,
     * so we don't make up profile data here.
     *
     * We use a generic signed-in state until the profile API
     * is implemented.
     */
    const firstLetter = "M";

    welcomeUser.textContent = "Welcome";
    greeting.textContent = "Welcome back";

    avatarButton.textContent = firstLetter;
    profileAvatar.textContent = firstLetter;

    profileName.textContent =
        "Your identity profile";

    /*
     * User menu
     */
    avatarButton.addEventListener("click", (event) => {
        event.stopPropagation();

        userMenu.hidden = !userMenu.hidden;
    });

    document.addEventListener("click", () => {
        userMenu.hidden = true;
    });

    userMenu.addEventListener("click", (event) => {
        event.stopPropagation();
    });

    logoutButton.addEventListener("click", () => {
        logout();
    });

    /*
     * These values remain placeholders until the backend
     * exposes profile/document statistics.
     */
    document.getElementById("documentCount").textContent = "—";
    document.getElementById("profileFieldCount").textContent = "—";


    /*
     * Dashboard navigation
     *
     * Connect the existing dashboard action buttons
     * to the corresponding frontend pages.
     */
    const navigationRoutes = {
        fill: "../autofill/autofill.html",
        upload: "../upload/upload.html",
        documents: "../upload/upload.html",
        profile: "../profile/profile.html"
    };

    document.querySelectorAll("[data-action]").forEach((button) => {
        button.addEventListener("click", () => {
            const action = button.dataset.action;
            const destination = navigationRoutes[action];

            if (destination) {
                window.location.href = destination;
            }
        });
    });
});