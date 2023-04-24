function setupChart(){
    dataModal = new bootstrap.Modal(document.getElementById("viewDataModal"));
    cData.teachers=new Set();
    cData.modParents=new Set();
    if(cData.modules.length>0){
        cData.modules.forEach((mod)=> addCombEvent(mod));
        setTeacherAllocTotal(cData.teachers, cData.modParents);
        setCombListeners();
        refreshClickListeners();
        enableTooltips();
    }

    $(".combingTableMod").each(function(){
        $(this).css("color", getTextColor($(this).attr("bgcolor")));
    });
}

function addCombEvent(mod){
    $(mod.session).append(`<div id="${mod.id}Div" session="${mod.session}" class="modDiv d-grid">
                                    <i id="${mod.id}-Remove" class="fas fa-xmark removeMod ${mod.group.parent.id}RemoveIcon"></i>
                                    <button id="${mod.id}" hx-get="/getModules/${mod.group.id}?calendar=1" hx-target="#modalBody" class="mod btn m-1 ${mod.group.parent.id}Class week${mod.group.period.week}">${mod.name}</button>
                                </div>`);
    $(`#${mod.id}`).css('background-color', mod.group.parent.color);
    $(`#${mod.id}, #${mod.id}-Remove`).css('color', getTextColor(mod.group.parent.color));
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
    htmx.process(htmx.find("#combingChart"));
}

$(document).on("click", ".removeMod", function(e){
    if($(this).hasClass('disabled')){
        $(this).removeClass('disabled');
        return;
    }
    let modId=this.id.split('-')[0];
    if(confirm('Unassign Teacher?')){
        htmx.ajax('POST', `/unassignTeacher/${modId}`);
    }
});

function checkAssignment(cellId){
    if($(cellId).find("button").length>1){
        $(cellId).find("button").addClass("bg-danger");
    }else {$(cellId).find("button").removeClass("bg-danger");}
}

function setTeacherAllocTotal(teachers, parents){
    updateSet=new Set();
    teachers.forEach(function(teacher){
        let modTotal=$(`#${teacher}Row`).find(`.mod`).length
        let tLoad=parseInt($(`#${teacher}TotalLoad`).text())
        $(`#${teacher}LoadChart`).text(tLoad-modTotal);
        if((tLoad-modTotal)<0){
            $(`#${teacher}LoadChart`).addClass("bg-danger");
        }
        else{
            $(`#${teacher}LoadChart`).removeClass("bg-danger");
        }
        parents.forEach(function(parent){
            let cTotal=$(`#${teacher}Row`).find(`.${parent}Class`).length
            $(`#${teacher}alloc${parent}`).text(cTotal);
            updateSet.add(`#${teacher}alloc${parent}`);
        })
        
        for(let i=1; i<=cData.numWeeks; i++){
            tTotal=$(`#${teacher}Row`).find(`.week${i}`).length
            load=parseInt($(`#${teacher}Load`).text());
            if((load-tTotal)<0){
                $(`#${teacher}Rem-${i}`).addClass("bg-danger");
            }
            else{
                $(`#${teacher}Rem-${i}`).removeClass("bg-danger");
            }

            $(`#${teacher}Allocated-${i}`).text(tTotal);
            $(`#${teacher}Rem-${i}`).text(load-tTotal);
            updateSet.add(`#${teacher}Rem-${i}`);
            updateSet.add(`#${teacher}Allocated-${i}`);
        }
    
    });
        parents.forEach(function(parent){
            let pTotal= $(`.${parent}Class`).length;
            $(`#${parent}Allocated`).text(pTotal);
            updateSet.add(`#${parent}Allocated`);
            if(parseInt($(`#${parent}Allocated`).text())==parseInt($(`#${parent}Total`).text())){
                $(`#${parent}Allocated`).addClass('bg-success');
            }else{
                $(`#${parent}Allocated`).removeClass('bg-success');
            }
        });

    updateSet.forEach(function(id){
        $(id).effect("highlight", 1000);
    })
}

htmx.on("htmx:afterSwap", (e) => {
    if(e.detail.target.id == "modalBody" && activePage=="combing") {
        $('.editBtnCol').remove();
        $("#modalBody").attr("hx-get",e.detail.pathInfo.requestPath);
        htmx.process(htmx.find("#modalBody"));
        dataModal.show();
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

$(document).on("updateColor", function(e){
    $(`.${e.detail.parentId}Class, .${e.detail.parentId}ClassHeader`).css("background-color",e.detail.color);
    $(`.${e.detail.parentId}Class, .${e.detail.parentId}ClassHeader, .${e.detail.parentId}RemoveIcon`).css("color",getTextColor(e.detail.color));
})

function setCombListeners(){
    $(document).on("modUpdate", function(e){
        $.each(e.detail.newMods, function(i,val){
            $(`#${val.id}Div`).remove();
            addCombEvent(val);
        });
        setTeacherAllocTotal(e.detail.teachers, e.detail.parents);
        refreshClickListeners();
    });
    
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
            htmx.ajax("POST", `/assignTeacherDrop/${teacher}/${mod}`).then(() => {
                checkAssignment($(ui.draggable).attr('session'))
            })
    }});
}