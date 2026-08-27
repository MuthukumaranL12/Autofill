const toast=document.getElementById("toast"),show=m=>{toast.textContent=m;toast.classList.add("show");clearTimeout(window.t);window.t=setTimeout(()=>toast.classList.remove("show"),2400)};
document.getElementById("previewButton").onclick=()=>show("Full document preview will open here.");
document.getElementById("reviewButton").onclick=()=>show("Field review will open here.");
document.getElementById("downloadButton").onclick=()=>show("Download will be connected to the generated file.");
document.getElementById("againButton").onclick=()=>location.href="../autofill/autofill.html";