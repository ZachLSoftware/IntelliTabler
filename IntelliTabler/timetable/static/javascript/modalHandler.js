const modal = new bootstrap.Modal(document.getElementById("addFormModal"));
var clickedDep = 0;

htmx.on("htmx:afterSwap", (e) => {
    if(e.detail.target.id == "addForm") {
        modal.show();
    }
})

htmx.on("htmx:beforeSwap", (e) => {
    if (e.detail.target.id == "addForm" && !e.detail.xhr.response){
        modal.hide();
        e.detail.shouldSwap = false;
    }
})

htmx.on("hidden.bs.modal", () => {
    $("#addForm").html("");
});

$(document).on("click", ".departmentButtons", function(){
    clickedDep=this.id.split('.')[0];
    console.log(clickedDep);
    $("#newTeacher").prop("hx-get", "/addTeacher/"+clickedDep);
    });

function getDep(){
    return clickedDep;
}

$("#newTeacher").on("click", function(){
    console.log(this.prop("hx-get"));
});