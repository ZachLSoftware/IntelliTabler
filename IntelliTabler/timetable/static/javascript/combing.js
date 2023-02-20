function setupChart(){
    dataModal = new bootstrap.Modal(document.getElementById("viewDataModal"));
    cData.teachers=new Set();
    cData.modParents=new Set();
    if(cData.modules.length>0){
        cData.modules.forEach((mod)=> addCombEvent(mod));
        setTeacherAllocTotal(cData.teachers, cData.modParents);
        setCombListeners();
        refreshClickListeners();
    }
}
function addCombEvent(mod){
    console.log(mod)
    $(mod.session).append(`<div id="${mod.id}Div" class="modDiv d-grid">
                                    <i id="${mod.id}-Remove" class="fas fa-xmark removeMod"></i>
                                    <button id="${mod.id}" hx-get="/getModules/${mod.group.id}?calendar=1" hx-target="#modalBody" class="mod btn m-1 ${mod.group.parent.id}Class">${mod.name}</button>
                                </div>`);
    $(`#${mod.id}`).css('background-color', mod.group.parent.color);
    $(`#${mod.id}`).css('color', getTextColor(mod.group.parent.color));
    //$(`#${mod.module.teacher}alloc${mod.module.parent}`).text(parseInt($(`#${mod.module.teacher}alloc${mod.module.parent}`).text())+1)
    cData.teachers.add(mod.teacher);
    cData.modParents.add(mod.group.parent.id);
    checkAssignment(mod.session);
        
        $(`#${mod.id}Div`).draggable({cancel:false,
                                    start: function(event, ui) {
                                        $(this).children().addClass('disabled');
                                    },
                                    stop: function(event, ui) {
                                        $(this).children('button').removeClass('disabled');
                                    },
                                    revert : function(e, ui){
                                        if ($(this).hasClass('drag-revert')) {
                                            $(this).removeClass('drag-revert');
                                            return true;
                                          }else{
                                            $(this).data("uiDraggable").originalPosition={
                                                top: 0,
                                                left:0
                                            };
                                            return !e;
                                          }
                                    }});
                                
};

function refreshClickListeners(){
    $(".removeMod").click(function(e){
        if($(this).hasClass('disabled')){
            $(this).removeClass('disabled');
            return;
        }
        let modId=this.id.split('-')[0];
        if(confirm('Unassign Teacher?')){
            htmx.ajax('POST', `/unassignTeacher/${modId}`);
        }
    });
    htmx.process(htmx.find("#combingChart"));
}


function checkAssignment(cellId){
    if($(cellId).find("button").length>1){
        $(cellId).find("button").addClass("bg-danger");
    }else {$(cellId).find("button").removeClass("bg-danger");}
}

function setTeacherAllocTotal(teachers, parents){
    teachers.forEach(function(teacher){
        parents.forEach(function(parent){
            let cTotal=$(`#${teacher}Row`).find(`.${parent}Class`).length
            $(`#${teacher}alloc${parent}`).text(cTotal).effect("highlight", 1000);
        })
        tTotal=$(`#${teacher}Row`).find(".mod").length
        load=parseInt($(`#${teacher}Load`).text());
        $(`#${teacher}Allocated`).text(tTotal).effect("highlight", 1000);
        $(`#${teacher}Rem`).text(load-tTotal).effect("highlight", 1000);
        parents.forEach(function(parent){
            let pTotal= $(`.${parent}Class`).length;
            $(`#${parent}Allocated`).text(pTotal).effect("highlight", 1000);
            if(parseInt($(`#${parent}Allocated`).text())==parseInt($(`#${parent}Total`).text())){
                $(`#${parent}Allocated`).addClass('bg-success');
            }else{
                $(`#${parent}Allocated`).removeClass('bg-success');
            }
        });
        //$(`#${teacher}Rem`).fadeOut8k("slow", function(){$(`#${teacher}Rem`).removeClass("bg-warning", 1000);});
    });


    // $(`#${mod.module.teacher}Rem`).text(parseInt($(`#${mod.module.teacher}Rem`).text())-1)
    // $(`#${mod.module.parent}Allocated`).text(parseInt($(`#${mod.module.parent}Allocated`).text())+1)
    // $(`#${mod.module.teacher}Allocated`).text(parseInt($(`#${mod.module.teacher}Allocated`).text())+1)
    // $(`#${mod.module.teacher}Rem`).text(parseInt($(`#${mod.module.teacher}Rem`).text())-1)
}

htmx.on("htmx:afterSwap", (e) => {
    if(e.detail.target.id == "modalBody" && activePage=="combing") {
        $('.editBtnCol').remove();
        dataModal.show();
    }else if(e.detail.target.id == "addForm" && activePage=="combing") {
        $('#moduleChoice').empty();
        let select=$('#groupChoice').find(':selected').val()
        $.each(cData.modChoices[select], function(index, val){
          $('#moduleChoice').append(`<option value='${val[0]}'>${val[1]}</option>`)
        })
        $('#groupChoice').change(function(){
            $('#moduleChoice').empty();
            let select=$('#groupChoice').find(':selected').val()
            $.each(cData.modChoices[select], function(index, val){
              $('#moduleChoice').append(`<option value='${val[0]}'>${val[1]}</option>`)
            })
        });
        modal.show();
    }
});


htmx.on("htmx:beforeSwap", (e) => {
    if (e.detail.target.id == "modalBody" && !e.detail.xhr.response && activePage=="combing"){
        dataModal.hide();
        e.detail.shouldSwap = false;
    }else if (e.detail.target.id == "addForm" && !e.detail.xhr.response && activePage=="combing"){
        modal.hide();
        e.detail.shouldSwap = false;
    }
})



function setCombListeners(){
    $(document).on("modUpdate", function(e){
        $.each(e.detail.newMods, function(i,val){
            $(`#${val.id}Div`).remove();
            addCombEvent(val);
        });
        setTeacherAllocTotal(e.detail.teachers, e.detail.parents);
        refreshClickListeners();
        // $(`#${e.detail.id}`).remove()
        // addCombEvent(e.detail);
        // refreshListeners();
    })
    $(document).on("unassignSuccess", function(e){
        $(`#${e.detail.modId}Div`).remove();
        setTeacherAllocTotal(e.detail.teacher, e.detail.parent);
    
    });
    $(".teacherRow").droppable({accept:".modDiv", drop: function(e, ui){
        teacher=this.id.split("Row")[0];
        mod=$(ui.draggable)[0].id.split("Div")[0]; 
        if($(ui.draggable).closest('tr')[0].id==this.id){
            $(ui.draggable).addClass('drag-revert');
        }else
            htmx.ajax("POST", `/assignTeacherDrop/${teacher}/${mod}`);
    }});
}
