refresh=false;
// $(document).ready(function(){
//     createCalendar();
// })
function createCalendar(id){
    dataModal = new bootstrap.Modal(document.getElementById("viewDataModal"));
    cData.calendarDiv=id;
    var numCal=$(".calendars").length;
    var days=['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']
    for(let week=1; week<=cData.weeks; week++){
        $(cData.calendarDiv).append(`<div id="calendarWeek-${week}" class="calendars" style="height: auto"></div>`)
    }
    $(".calendars").hide()
    $("#calendarWeek-1").addClass("activeCalendar");
    $("#calendarWeek-1").show()

    setActive();

    $(".calendars").each(function(index){
        week=this.id.split('-')[1]
        $(this).append(`<div id="periodColumn-${week}" class="dayHeader periodColumn"><div class="calendarHeader"><h3>Period</h3></div></div>`)
        days.forEach((day) =>{
            $(this).append(`<div id="${day}Header-${week}" class="dayHeader"><div class="calendarHeader"><h3>${day}</h3></div></div>`);
            for(let period=1; period<=cData.periods; period++){
                $(`#${day}Header-${week}`).append(`<div id="${day}-${period}-${week}" class="dayCell"></div>`);
                if(day=="Fri"){$(`#${day}Header-${week}`).addClass("endColumn")}

                $(`#${day}-${period}-${week}`).droppable({accept:".event", drop: function(e, ui){        
                    $(ui.draggable).appendTo(this);
                    $(ui.draggable).css({'top' : 0, 'left' : 0})
                    p=this.id.split('-')
                    var element = htmx.ajax('POST', `/calendarPeriodDrop/${p[0]}-${p[1]}/${p[2]}/${ui.draggable[0].id}`);
                    }
                });
            }
        });

            for(let period=1; period<=cData.periods; period++){
                $(`#periodColumn-${week}`).append(`<div class="pRow">${period}</div>`);
            }

        })
        $(".dayHeader").css("grid-template-rows", `1fr repeat(${cData.periods}, 3fr`);


    cData.events["modules"].forEach((mod) => addCalEvent(mod));
    refreshListeners();
    $(".dayCell").on("click", function(e){
        if(this!=e.target){
            return false;
        }
        var id=this.id.split('-');
        if(!cData.teacher){
        
            htmx.ajax('GET', `/addModuleCalendar/${id[0]}-${id[1]}/${id[2]}/${cData.timetable}`, '#addForm');
        }
    })

    $('#next').click(function(){
        var current=$(".activeCalendar")[0];
        let nextId=parseInt(calendar.id.split('-')[1])+1;
        var next=$("#calendarWeek-"+nextId);
        $(current).hide("slide", { direction: "left", duration: 500 });
        $(next).show("slide", { direction: "right", duration: 500});
         $(current).removeClass("activeCalendar");
        $(next).addClass("activeCalendar");
        setActive();
    })
    $('#previous').click(function(){
        var current=$(".activeCalendar")[0];
        let nextId=parseInt(calendar.id.split('-')[1])-1;
        var next=$("#calendarWeek-"+nextId);
        $(current).hide("slide", { direction: "right" }, 500);
        $(next).show("slide", { direction: "left" }, 500);
         $(current).removeClass("activeCalendar");
        $(next).addClass("activeCalendar");
        setActive();
    })
    
}

function addCalEvent(mod){
        $(`#${mod.period.name}-${mod.period.week}`).append(`<button id="${mod.id}" hx-get="/getModules/${mod.groupid}?calendar=1" hx-target="#modalBody" class="event btn m-1 ${mod.parent.id}">${mod.name}</button>`);
        $(`#${mod.id}`).css('background-color', mod.parent.color);
        $(`#${mod.id}`).css('color',getTextColor(mod.parent.color));
        if(!cData.teacher){
            
            $(`#${mod.id}`).draggable({cancel:false,
                                        revert : function(e, ui){
                                            $(this).data("uiDraggable").originalPosition={
                                                top: 0,
                                                left:0
                                            };
                                            return !e;
                                        }});
                                    }
    };





function filterById(jsonObject, id) {
    return jsonObject.filter(function(jsonObject) {
        return (jsonObject['id'] == id);})[0]
        ;}

function setActive(){
    calendar = $(".activeCalendar")[0];
    var week=calendar.id.split('-')[1]
    $("#title").text("Calendar Week " + week)
    $(".arrows").css('opacity',1).prop('disabled', false)
    if(week==1){
        $("#previous").css('opacity',0.5).prop('disabled', true)  
    }if (week==$(".calendars").length){
        $("#next").css('opacity',0.5).prop('disabled', true)  
    }
}

function refreshListeners(){
    htmx.process(htmx.find(cData.calendarDiv));   
    
}

$(cData.calendarDiv).on("click", ".event", function(e){
    clicked=this.id;
    e.stopPropagation();
});

htmx.on("htmx:afterSwap", (e) => {
    if(e.detail.target.id == "modalBody") {
        if (cData.teacher){
            $(".editBtnCol").remove()
        }
        dataModal.show();
    }
})

htmx.on("htmx:beforeSwap", (e) => {
    if (e.detail.target.id == "modalBody" && !e.detail.xhr.response){
        dataModal.hide();
        e.detail.shouldSwap = false;
    }
})


$(document).on("addCalendarEvent", function(e){
    e.detail.modules.forEach((mod) => addCalEvent(mod));
    refreshListeners();
})

$(document).on("periodUpdate", function(e){
    console.log(e.detail)
    e.detail.modules.forEach((mod) => {
        $(`#${mod.id}`).remove()
        addCalEvent(mod);
    });

    refreshListeners();
})

$(document).on("updateColor",function(e){
    $(`.${e.detail.parentId}`).css("background-color", e.detail.color);
    $(`.${e.detail.parentId}`).css("color", getTextColor(e.detail.color));
})