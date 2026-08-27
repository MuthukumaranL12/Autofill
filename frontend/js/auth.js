// frontend/js/auth.js

function saveAccessToken(token) {
    localStorage.setItem("access_token", token);
}

function getAccessToken() {
    return localStorage.getItem("access_token");
}

function isAuthenticated() {
    return Boolean(getAccessToken());
}

function logout() {
    localStorage.removeItem("access_token");
    window.location.href = "../login/login.html";
}

/**
 * Use this at the beginning of protected pages.
 */
function requireAuthentication() {
    if (!isAuthenticated()) {
        window.location.href = "../login/login.html";
    }
}

/**
 * Use this on login/register pages if you don't want an already
 * authenticated user to see them.
 */
function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        window.location.href = "../dashboard/dashboard.html";
    }
}
