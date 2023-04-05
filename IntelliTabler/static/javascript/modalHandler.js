const modal = new bootstrap.Modal(document.getElementById("addFormModal"));
var clicked = 0;
var clickedChild=0;

htmx.on("htmx:afterSwap", (e) => {
    if(e.detail.target.id == "addForm") {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
        console.log(tooltipList)
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

$(document).on("click", ".parentButtons, .childButtons", function(){
    if($(this).hasClass("childButtons")){
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

