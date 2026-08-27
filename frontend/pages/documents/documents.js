// frontend/pages/documents/documents.js

document.addEventListener("DOMContentLoaded", () => {
    requireAuthentication();

    /*
     * No GET /api/documents endpoint exists in the current
     * document_routes.py, so there is intentionally no fetch here.
     *
     * Once the backend exposes something such as:
     *
     * GET /api/documents/
     *
     * we can replace this page with the real document list.
     */
});
