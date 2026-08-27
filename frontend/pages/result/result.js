if (typeof requireAuthentication === "function") {
  requireAuthentication();
}

const previewButton = document.getElementById("previewButton");
const reviewButton = document.getElementById("reviewButton");
const downloadButton = document.getElementById("downloadButton");
const againButton = document.getElementById("againButton");
const toast = document.getElementById("toast");

const RESULT_DB_NAME = "medform_autofill";
const RESULT_STORE_NAME = "results";
const RESULT_KEY = "latest";

let resultUrl = null;
let resultRecord = null;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");

  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => {
    toast.classList.remove("show");
  }, 2400);
}

function openResultDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(RESULT_DB_NAME, 1);

    request.onupgradeneeded = () => {
      const db = request.result;

      if (!db.objectStoreNames.contains(RESULT_STORE_NAME)) {
        db.createObjectStore(RESULT_STORE_NAME);
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () =>
      reject(request.error || new Error("Unable to open result storage."));
  });
}

async function getResult() {
  const db = await openResultDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(
      RESULT_STORE_NAME,
      "readonly"
    );

    const store = transaction.objectStore(RESULT_STORE_NAME);
    const request = store.get(RESULT_KEY);

    request.onsuccess = () => {
      db.close();
      resolve(request.result || null);
    };

    request.onerror = () => {
      db.close();
      reject(
        request.error ||
          new Error("Unable to retrieve the completed form.")
      );
    };
  });
}

async function deleteResult() {
  const db = await openResultDatabase();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(
      RESULT_STORE_NAME,
      "readwrite"
    );

    transaction.objectStore(RESULT_STORE_NAME).delete(RESULT_KEY);

    transaction.oncomplete = () => {
      db.close();
      resolve();
    };

    transaction.onerror = () => {
      db.close();
      reject(transaction.error);
    };
  });
}

function buildDownloadName(originalName) {
  const safeOriginalName = originalName || "form";
  const baseName = safeOriginalName.replace(/\.[^/.]+$/, "");

  return `Completed_${baseName}.png`;
}

function displayResult(record) {
  if (!record || !(record.blob instanceof Blob)) {
    return false;
  }

  resultRecord = record;
  resultUrl = URL.createObjectURL(record.blob);

  const previewImage = document.getElementById(
    "resultPreviewImage"
  );

  previewImage.src = resultUrl;
  previewImage.alt = `Completed ${record.originalName || "form"}`;

  const resultFileName = document.getElementById(
    "resultFileName"
  );

  if (resultFileName) {
    resultFileName.textContent = buildDownloadName(
      record.originalName
    );
  }

  return true;
}

async function initializePage() {
  try {
    const record = await getResult();

    if (!displayResult(record)) {
      showToast(
        "No completed form was found. Please start autofill again."
      );

      setTimeout(() => {
        window.location.href = "../autofill/autofill.html";
      }, 1200);

      return;
    }
  } catch (error) {
    console.error("Unable to load autofill result:", error);

    showToast(
      "Unable to load the completed form. Please try again."
    );

    setTimeout(() => {
      window.location.href = "../autofill/autofill.html";
    }, 1200);
  }
}

previewButton.addEventListener("click", () => {
  if (!resultUrl) {
    showToast("The completed form is not available.");
    return;
  }

  window.open(resultUrl, "_blank", "noopener,noreferrer");
});

reviewButton.addEventListener("click", () => {
  showToast(
    "Please review the completed form carefully before submitting it."
  );
});

downloadButton.addEventListener("click", () => {
  if (!resultUrl || !resultRecord) {
    showToast("The completed form is not available.");
    return;
  }

  const link = document.createElement("a");

  link.href = resultUrl;
  link.download = buildDownloadName(
    resultRecord.originalName
  );

  document.body.appendChild(link);
  link.click();
  link.remove();
});

againButton.addEventListener("click", async () => {
  try {
    if (resultUrl) {
      URL.revokeObjectURL(resultUrl);
      resultUrl = null;
    }

    await deleteResult();
  } catch (error) {
    console.error("Unable to clear previous result:", error);
  }

  window.location.href = "../autofill/autofill.html";
});

window.addEventListener("beforeunload", () => {
  if (resultUrl) {
    URL.revokeObjectURL(resultUrl);
  }
});

initializePage();
