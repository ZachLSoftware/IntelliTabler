var calendar;
var selectedCell;
var numCal=$(".calendars").length;
let days=['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']
refresh=false;
$(document).ready(function(){
    createCalendar();
})


function createCalendar(){
    for(let week=1; week<=weeks; week++){
        $("#calendarWrapper").append(`<div id="calendarWeek-${week}" class="calendars" style="height: 1000px"></div>`)
    }
    $(".calendars").hide()
    $("#calendarWeek-1").addClass("activeCalendar");
    $("#calendarWeek-1").show()

    setActive();

    $(".calendars").each(function(index){
        week=this.id.split('-')[1]
        $(this).append(`<div id="periodColumn-${week}" class="dayHeader periodColumn border"><div class="calendarHeader"><h3>Period</h3></div></div>`)
        days.forEach((day) =>{
            $(this).append(`<div id="${day}Header-${week}" class="dayHeader border"><div class="calendarHeader"><h3>${day}</h3></div></div>`);
            for(let period=1; period<=periods; period++){
                $(`#${day}Header-${week}`).append(`<div id="${day}-${period}-${week}" class="border dayCell">${day}-${period}<br/></div>`);
                $(`#${day}-${period}-${week}`).droppable({accept:".event", drop: function(e, ui){        
                    $(ui.draggable).appendTo(this);
                    $(ui.draggable).css({'top' : 0, 'left' : 0})
                    p=this.id.split('-')
                    var element = htmx.ajax('POST', `/calendarPeriodDrop/${p[0]}-${p[1]}/${p[2]}/${ui.draggable[0].id}`);
                    }
                });
            }
        });

            for(let period=1; period<=periods; period++){
                $(`#periodColumn-${week}`).append(`<div class="border pRow">${period}</div>`);
            }

        })
        $(".dayHeader").css("grid-template-rows", `1fr repeat(${periods}, 3fr`);


    events["modules"].forEach((mod) => addEvent(mod));
    refreshListeners();
    $(".dayCell").on("click", function(e){
        var id=this.id.split('-');
        htmx.ajax('GET', `/addModuleCalendar/${id[0]}-${id[1]}/${id[2]}/${year}`, '#addForm');
    })
    
}

function addEvent(mod){
        $(`#${mod.module.period}-${mod.module.week}`).append(`<button id="${mod.id}" hx-get="/getModules/${mod.module.groupid}?calendar=1" hx-target="#modalBody" class="event btn m-1">${mod.module.name}</button>`);
        $(`#${mod.id}`).css('background-color', mod.module.color);
        if(!teacher){
            
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

function filterById(jsonObject, id) {
    return jsonObject.filter(function(jsonObject) {
        return (jsonObject['id'] == id);})[0]
        ;}

function setActive(){
    calendar = $(".activeCalendar")[0];
    var week=calendar.id.split('-')[1]
    $("#title").text("Calendar Week " + week)
    $(".arrows").css('opacity',1).prop('disabled', false)
    console.log(week==$(".calendars").length)
    console.log($(".calendars").length)
    if(week==1){
        $("#previous").css('opacity',0.5).prop('disabled', true)  
    }else if (week==$(".calendars").length){
        $("#next").css('opacity',0.5).prop('disabled', true)  
    }
}

const dataModal = new bootstrap.Modal(document.getElementById("viewDataModal"));

function refreshListeners(){
    $(".event").on("click", function(e){
        clicked=this.id;
        e.stopPropagation();
    });
 
    htmx.process(htmx.find("#calendarWrapper"));
}

htmx.on("htmx:afterSwap", (e) => {
    if(e.detail.target.id == "modalBody") {
        if (teacher){
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

$(document).on("addEvent", function(e){
    addEvent(e.detail.modules[0]);
    refreshListeners();
})

$(document).on("periodUpdate", function(e){
    $(`#${e.detail.id}`).remove()
    addEvent(e.detail);
    refreshListeners();
})