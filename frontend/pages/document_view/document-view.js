const edit=document.getElementById("editButton"),fields=[...document.querySelectorAll(".field input")],toast=document.getElementById("toast"),del=document.getElementById("deleteButton"),preview=document.getElementById("previewButton");
function show(m){toast.textContent=m;toast.classList.add("show");clearTimeout(window.t);window.t=setTimeout(()=>toast.classList.remove("show"),2400)}
edit.addEventListener("click",()=>{const on=fields[0].disabled;fields.forEach(f=>f.disabled=!on);edit.textContent=on?"Save":"Edit";if(!on)show("Document details are ready to edit.");else show("Document details saved locally.")});
del.addEventListener("click",()=>show("Delete will be connected to the backend."));
preview.addEventListener("click",()=>show("Document preview will open here."));