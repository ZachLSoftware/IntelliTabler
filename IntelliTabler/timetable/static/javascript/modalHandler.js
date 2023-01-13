const modal = new bootstrap.Modal(document.getElementById("addFormModal"));
var clicked = 0;
var clickedChild=0;

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

$(document).on("click", ".departmentButtons, .yearButtons, .moduleButtons, .teacherButtons", function(){
    if($(this).hasClass("moduleButtons") || $(this).hasClass("teacherButtons")){
        clickedChild=this.id.split('.')[0]
        console.log(clickedChild);
    }else{
        clicked=this.id.split('.')[0];
        console.log(clicked);
    }
    
    });

function getClicked(){
    return clicked;
}

function getChild(){
    return clickedChild;
}

document.body.addEventListener("deleted", function(e){
    alert('Delete triggered');
})