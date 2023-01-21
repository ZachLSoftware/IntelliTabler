var calendar;
var selectedCell;
var numCal=$(".calendars").length;
let days=['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']
refresh=false;

for(let week=1; week<=weeks; week++){
    $("#calendarWrapper").append(`<div id="calendarWeek-${week}" class="d-none calendars" style="height: 1000px"></div>`)
}
$("#calendarWeek-1").removeClass("d-none").addClass("activeCalendar");
setActive();

$(".calendars").each(function(index){
    week=this.id.split('-')[1]
    $(this).append(`<div id="periodColumn-${week}" class="dayHeader border periodColumn"><div class="calendarHeader"><h3>Period</h3></div></div>`)
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
function addEvent(mod){
        $(`#${mod.module.period}-${mod.module.week}`).append(`<button id="${mod.id}" hx-get="/getModules/${mod.module.parent}?calendar=1" hx-target="#modalBody" class="event btn btn-info">${mod.module.name}</button>`);
        $(`#${mod.id}`).draggable({cancel:false,
                                    revert : function(e, ui){
                                        $(this).data("uiDraggable").originalPosition={
                                            top: 0,
                                            left:0
                                        };
                                        return !e;
                                    }});
    };

$(".dayCell").on("click", function(e){
    var id=this.id.split('-');
    htmx.ajax('GET', `/addModuleCalendar/${id[0]}-${id[1]}/${id[2]}/${year}`, '#addForm');
})


$('#next').click(function(){
    var current=$(".activeCalendar")[0];
    let nextId=parseInt(calendar.id.split('-')[1])+1;
    var next=$("#calendarWeek-"+nextId);
    $(current).removeClass("activeCalendar").addClass("d-none");
    $(next).removeClass("d-none").addClass("activeCalendar");
    setActive();
})
$('#previous').click(function(){
    var current=$(".activeCalendar")[0];
    let nextId=parseInt(calendar.id.split('-')[1])-1;
    var next=$("#calendarWeek-"+nextId);
    $(current).removeClass("activeCalendar").addClass("d-none");
    $(next).removeClass("d-none").addClass("activeCalendar");
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
}

htmx.on("htmx:afterSwap", (e) => {
    if(e.detail.target.id == "modalBody") {
        $("#assignPeriod").remove()
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
    htmx.process(htmx.find("#calendarWrapper"));
    refreshListeners();
})

