//$('#combingWrapper').css("grid-template-columns", `repeat(${numP}, 1fr`);
const dataModal = new bootstrap.Modal(document.getElementById("viewDataModal"));
modules.forEach((mod)=> addEvent(mod));
function addEvent(mod){
    $(mod.module.session).append(`<button id="${mod.id}" hx-get="/getModules/${mod.module.groupid}?calendar=1" hx-target="#modalBody" class="event btn m-1">${mod.module.name}</button>`);
    $(`#${mod.id}`).css('background-color', mod.module.color);
    $(`#${mod.module.parent}Allocated`).text(parseInt($(`#${mod.module.parent}Allocated`).text())+1)
    $(`#${mod.module.teacher}Allocated`).text(parseInt($(`#${mod.module.teacher}Allocated`).text())+1)
    $(`#${mod.module.teacher}Rem`).text(parseInt($(`#${mod.module.teacher}Rem`).text())-1)
    $(`#${mod.module.teacher}alloc${mod.module.parent}`).text(parseInt($(`#${mod.module.teacher}alloc${mod.module.parent}`).text())+1)

    checkAssignment(mod.module.session);
    if(parseInt($(`#${mod.module.parent}Allocated`).text())==parseInt($(`#${mod.module.parent}Total`).text())){
        $(`#${mod.module.parent}Allocated`).addClass('bg-success');
    }
        
        $(`#${mod.id}`).draggable({cancel:false,
                                    revert : function(e, ui){
                                        $(this).data("uiDraggable").originalPosition={
                                            top: 0,
                                            left:0
                                        };
                                        return !e;
                                    }});
                                
};

function checkAssignment(cellId){
    if($(cellId).children().length>1){
        $(cellId).children().addClass("bg-danger");
    }
}

htmx.on("htmx:afterSwap", (e) => {
    if(e.detail.target.id == "modalBody") {
        $('.editBtnCol').remove();
        dataModal.show();
    }
})

htmx.on("htmx:beforeSwap", (e) => {
    if (e.detail.target.id == "modalBody" && !e.detail.xhr.response){
        dataModal.hide();
        e.detail.shouldSwap = false;
    }
})