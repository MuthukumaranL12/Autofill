const toast = document.getElementById("toast");

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");

  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => {
    toast.classList.remove("show");
  }, 2400);
}

document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", () => {
    const action = button.dataset.action;

    if (action === "upload") {
      showToast("Document upload screen will open here.");
    }

    if (action === "fill") {
      showToast("Form autofill screen will open here.");
    }

    if (action === "documents") {
      showToast("Document history will open here.");
    }
  });
});

document.querySelectorAll(".nav-link:not(.logout)").forEach((link) => {
  link.addEventListener("click", () => {
    document.querySelectorAll(".nav-link").forEach((item) => item.classList.remove("active"));
    link.classList.add("active");
  });
});

document.getElementById("logoutBtn").addEventListener("click", () => {
  showToast("Logout will be connected to the backend.");
});
