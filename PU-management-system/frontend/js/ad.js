function toggleProfileMenu(){

let menu = document.getElementById("profileDropdown");

menu.style.display = menu.style.display === "flex" ? "none" : "flex";

}

// Avatar upload
const avatar = document.getElementById("userAvatar");
const upload = document.getElementById("imageUpload");

avatar.addEventListener("click", function(e){
e.stopPropagation();
upload.click();
});

upload.addEventListener("change", function(){

const file = this.files[0];

if(file){

const reader = new FileReader();

reader.onload = function(e){
avatar.innerHTML = `<img src="${e.target.result}">`;
}

reader.readAsDataURL(file);

}

});