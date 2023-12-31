function setupChart(){
    dataModal = new bootstrap.Modal(document.getElementById("viewDataModal")); //Set data modal
    cData.teachers=new Set(); //Empty teacher set
    cData.modParents=new Set(); //Empty parent set
    if(cData.modules.length>0){
        cData.modules.forEach((mod)=> addCombEvent(mod)); //Add events to chart
        setTeacherAllocTotal(cData.teachers, cData.modParents); //Update allocation
        setCombListeners(); //Setup listeners
        refreshClickListeners(); //Refresh htmx listeners
        enableTooltips();
    }

    //Fix any text colors
    $(".combingTableMod").each(function(){
        $(this).css("color", getTextColor($(this).attr("bgcolor")));
    });
}

//Adds events to the chart.
function addCombEvent(mod){
    //Create and append combing element
    $(mod.session).append(`<div id="${mod.id}Div" session="${mod.session}" class="modDiv d-grid">
                                    <i id="${mod.id}-Remove" class="fas fa-xmark removeMod ${mod.group.parent.id}RemoveIcon"></i>
                                    <button id="${mod.id}" hx-get="/getModules/${mod.group.id}?calendar=1" hx-target="#modalBody" class="mod btn m-1 ${mod.group.parent.id}Class week${mod.group.period.week}">${mod.name}</button>
                                </div>`);
    
    //set colors
    $(`#${mod.id}`).css('background-color', mod.group.parent.color);
    $(`#${mod.id}, #${mod.id}-Remove`).css('color', getTextColor(mod.group.parent.color));
    
    //Add to teachers and parents
    cData.teachers.add(mod.teacher);
    cData.modParents.add(mod.group.parent.id);

    //Check if assignment has caused a conflict
    checkAssignment(mod.session);
        
    //Set draggable listener
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

//Refresh htmx
function refreshClickListeners(){
    htmx.process(htmx.find("#combingChart"));
};

//Check if assignment conflicts with another class.
function checkAssignment(cellId){
    if($(cellId).find("button").length>1){
        $(cellId).find("button").addClass("bg-danger");
    }else {$(cellId).find("button").removeClass("bg-danger");}
};

//Sets totals for allocation tables.
function setTeacherAllocTotal(teachers, parents){
    updateSet=new Set(); //Empty set for update animation

    //Update each teacher
    teachers.forEach(function(teacher){

        //Get Teacher load and how many classes are assigned.
        let modTotal=$(`#${teacher}Row`).find(`.mod`).length
        let tLoad=parseInt($(`#${teacher}TotalLoad`).text())
        $(`#${teacher}LoadChart`).text(tLoad-modTotal); //Set remaining load

        //Set background to red if overloaded.
        if((tLoad-modTotal)<0){
            $(`#${teacher}LoadChart`).addClass("bg-danger");
        }
        else{
            $(`#${teacher}LoadChart`).removeClass("bg-danger");
        }

        //Update each parent module cell in the teacher allocation table
        parents.forEach(function(parent){
            let cTotal=$(`#${teacher}Row`).find(`.${parent}Class`).length
            $(`#${teacher}alloc${parent}`).text(cTotal);
            updateSet.add(`#${teacher}alloc${parent}`);
        })
        
        //Update each weeks load allocation for the teacher
        for(let i=1; i<=cData.numWeeks; i++){
            tTotal=$(`#${teacher}Row`).find(`.week${i}`).length
            load=parseInt($(`#${teacher}Load`).text());
            if((load-tTotal)<0){
                $(`#${teacher}Rem-${i}`).addClass("bg-danger");
            }
            else{
                $(`#${teacher}Rem-${i}`).removeClass("bg-danger");
            }

            //Set totals
            $(`#${teacher}Allocated-${i}`).text(tTotal);
            $(`#${teacher}Rem-${i}`).text(load-tTotal);
            updateSet.add(`#${teacher}Rem-${i}`);
            updateSet.add(`#${teacher}Allocated-${i}`);
        }
    
    });

    //Update class alocation table
    parents.forEach(function(parent){
        //Get totals and update each class
        let pTotal= $(`.${parent}Class`).length;
        $(`#${parent}Allocated`).text(pTotal);
        updateSet.add(`#${parent}Allocated`);

        //Check if fully allowcated and add green background.
        if(parseInt($(`#${parent}Allocated`).text())==parseInt($(`#${parent}Total`).text())){
            $(`#${parent}Allocated`).addClass('bg-success');
        }else{
            $(`#${parent}Allocated`).removeClass('bg-success');
        }
    });

    //Add a highlight effect to show which elements have been changed.
    updateSet.forEach(function(id){
        $(id).effect("highlight", 1000);
    })
};


//Sets up listeners for the chart.
function setCombListeners(){
    //Updates colors based on parent class.
    $(document).on("updateColor", function(e){
        $(`.${e.detail.parentId}Class, .${e.detail.parentId}ClassHeader`).css("background-color",e.detail.color);
        $(`.${e.detail.parentId}Class, .${e.detail.parentId}ClassHeader, .${e.detail.parentId}RemoveIcon`).css("color",getTextColor(e.detail.color));
    });

    //Sets up the x remove mod icon listener.
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

    //Listens for updates.
    $(document).on("modUpdate", function(e){
        $.each(e.detail.newMods, function(i,val){
            $(`#${val.id}Div`).remove(); //Remove element before re-adding.
            addCombEvent(val);
        });
        setTeacherAllocTotal(e.detail.teachers, e.detail.parents); //Update allocations
        refreshClickListeners();
    });
    
    //Removes element when unassigned
    $(document).on("unassignSuccess", function(e){
        $(`#${e.detail.modId}Div`).remove();
        setTeacherAllocTotal(e.detail.teacher, e.detail.parent);
    
    });

    //Sets up droppable listeners to assign classes to teachers
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