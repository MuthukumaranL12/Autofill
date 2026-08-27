const toast = document.getElementById("toast"),
  show = (m) => {
    toast.textContent = m;
    toast.classList.add("show");
    clearTimeout(window.t);
    window.t = setTimeout(() => toast.classList.remove("show"), 2200);
  };
document
  .querySelectorAll(".switch input")
  .forEach((i) =>
    i.addEventListener("change", () =>
      show(i.checked ? "Permission enabled." : "Permission disabled."),
    ),
  );
document.getElementById("clearButton").onclick = () =>
  show("Consent history will be managed by the backend.");
