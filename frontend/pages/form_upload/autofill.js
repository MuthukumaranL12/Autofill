const fileInput = document.getElementById("fileInput");
const chooseButton = document.getElementById("chooseButton");
const dropZone = document.getElementById("dropZone");
const selectedFile = document.getElementById("selectedFile");
const fileName = document.getElementById("fileName");
const fileSize = document.getElementById("fileSize");
const fileIcon = document.getElementById("fileIcon");
const removeButton = document.getElementById("removeButton");
const startButton = document.getElementById("startButton");

const uploadView = document.getElementById("uploadView");
const processingView = document.getElementById("processingView");
const resultView = document.getElementById("resultView");

const progressBar = document.getElementById("progressBar");
const progressPercent = document.getElementById("progressPercent");
const processingStatus = document.getElementById("processingStatus");

const stepUpload = document.getElementById("stepUpload");
const stepProcess = document.getElementById("stepProcess");
const stepResult = document.getElementById("stepResult");

const processItems = [
  document.getElementById("process1"),
  document.getElementById("process2"),
  document.getElementById("process3"),
  document.getElementById("process4")
];

const resultFileName = document.getElementById("resultFileName");
const newFormButton = document.getElementById("newFormButton");
const downloadButton = document.getElementById("downloadButton");
const toast = document.getElementById("toast");

let selectedForm = null;
let processingTimer = null;

const allowedTypes = [
  "application/pdf",
  "image/png",
  "image/jpeg"
];

const maxFileSize = 10 * 1024 * 1024;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");

  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => {
    toast.classList.remove("show");
  }, 2500);
}

function formatSize(bytes) {
  if (bytes < 1024 * 1024) {
    return `${Math.round(bytes / 1024)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function setFile(file) {
  if (!allowedTypes.includes(file.type)) {
    showToast("Please choose a PDF, JPG, JPEG or PNG file.");
    return;
  }

  if (file.size > maxFileSize) {
    showToast("The selected file is larger than 10 MB.");
    return;
  }

  selectedForm = file;

  fileName.textContent = file.name;
  fileSize.textContent = formatSize(file.size);
  fileIcon.textContent = file.type === "application/pdf" ? "PDF" : "IMG";

  selectedFile.hidden = false;
  startButton.disabled = false;
}

function removeFile() {
  selectedForm = null;
  selectedFile.hidden = true;
  startButton.disabled = true;
  fileInput.value = "";
}

chooseButton.addEventListener("click", () => {
  fileInput.click();
});

fileInput.addEventListener("change", () => {
  if (fileInput.files.length) {
    setFile(fileInput.files[0]);
  }

  fileInput.value = "";
});

removeButton.addEventListener("click", removeFile);

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("drag-over");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("drag-over");
  });
});

dropZone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];

  if (file) {
    setFile(file);
  }
});

function updateSteps(stage) {
  stepUpload.classList.remove("active", "complete");
  stepProcess.classList.remove("active", "complete");
  stepResult.classList.remove("active", "complete");

  if (stage === "upload") {
    stepUpload.classList.add("active");
  }

  if (stage === "process") {
    stepUpload.classList.add("complete");
    stepProcess.classList.add("active");
  }

  if (stage === "result") {
    stepUpload.classList.add("complete");
    stepProcess.classList.add("complete");
    stepResult.classList.add("active");
  }
}

function startProcessing() {
  if (!selectedForm) {
    showToast("Please select a form first.");
    return;
  }

  uploadView.hidden = true;
  processingView.hidden = false;
  resultView.hidden = true;

  updateSteps("process");

  processItems.forEach((item) => item.classList.remove("done"));

  let progress = 0;
  let stage = 0;

  processingStatus.textContent = "Reading document...";
  progressBar.style.width = "0%";
  progressPercent.textContent = "0%";

  clearInterval(processingTimer);

  processingTimer = setInterval(() => {
    progress += Math.floor(Math.random() * 8) + 5;

    if (progress >= 100) {
      progress = 100;
    }

    progressBar.style.width = `${progress}%`;
    progressPercent.textContent = `${progress}%`;

    if (progress >= 20 && stage < 1) {
      processItems[0].classList.add("done");
      processingStatus.textContent = "Detecting form fields...";
      stage = 1;
    }

    if (progress >= 45 && stage < 2) {
      processItems[1].classList.add("done");
      processingStatus.textContent = "Matching profile information...";
      stage = 2;
    }

    if (progress >= 72 && stage < 3) {
      processItems[2].classList.add("done");
      processingStatus.textContent = "Generating completed form...";
      stage = 3;
    }

    if (progress >= 100) {
      processItems[3].classList.add("done");
      clearInterval(processingTimer);

      setTimeout(showResult, 500);
    }
  }, 450);
}

function showResult() {
  processingView.hidden = true;
  resultView.hidden = false;

  updateSteps("result");

  resultFileName.textContent = `Completed — ${selectedForm.name}`;
}

startButton.addEventListener("click", startProcessing);

newFormButton.addEventListener("click", () => {
  selectedForm = null;
  selectedFile.hidden = true;
  startButton.disabled = true;
  fileInput.value = "";

  resultView.hidden = true;
  processingView.hidden = true;
  uploadView.hidden = false;

  updateSteps("upload");
});

downloadButton.addEventListener("click", () => {
  // Static placeholder — connect this to the completed file returned by FastAPI later.
  showToast("Download will be connected to the generated form.");
});
