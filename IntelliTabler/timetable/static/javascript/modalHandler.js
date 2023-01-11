const modal = new bootstrap.Modal(document.getElementById("addFormModal"));
var clicked = 0;

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

$(document).on("click", ".departmentButtons, .yearButtons", function(){
    clicked=this.id.split('.')[0];
    console.log(clicked);
    if($(this).hasClass('yearButtons')){
        $("#newModuleGroup").prop("hx-get", "/addModule/"+clicked);
    }
    $("#newTeacher").prop("hx-get", "/addTeacher/"+clicked);
    });

function getClicked(){
    return clicked;
}

$("#newTeacher").on("click", function(){
    console.log(this.prop("hx-get"));
});