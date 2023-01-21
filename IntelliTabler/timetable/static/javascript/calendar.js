var calendar;
var numCal=$(".calendars").length;
for(let week=1; week<=weeks; week++){
    $("#calendarWrapper").append(`<div id="calendarWeek-${week}" class="d-none calendars" style="height: 1000px"></div>`)
}
$("#calendarWeek-1").removeClass("d-none").addClass("activeCalendar");
setActive();




let days=['Mon', 'Tues', 'Wed', 'Thurs', 'Fri']

$(".calendars").each(function(index){
    week=this.id.split('-')[1]
    $(this).append(`<div id="periodColumn-${week}" class="dayHeader border"><h3>Period</h3></div>`)
    days.forEach((day) =>{
        $(this).append(`<div id="${day}Header-${week}" class="dayHeader border"><h3>${day}</h3></div>`);
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
        $(`#periodColumn-${week}`).append(`<div id="${period}Row" class="border">Period - ${period}</div>`);
    }

})

$(".dayHeader").css("grid-template-rows", `repeat(${periods+1}, 1fr`);


events["modules"].forEach((mod)=>{
    $(`#${mod.module.period}-${mod.module.week}`).append(`<button id="${mod.id}" hx-get="/getModules/${mod.module.parent}?calendar=1" hx-target="#modalBody" class="event btn btn-info">${mod.module.name}</button>`);
    $(`#${mod.id}`).draggable({cancel:false,
                                revert : function(e, ui){
                                    $(this).data("uiDraggable").originalPosition={
                                        top: 0,
                                        left:0
                                    };
                                    return !e;
                                }});
})

$(".dayCell").on("click", function(e){
    $(this).addClass("bg-primary");
})

// $(".event").on("click", function(e){
//     var test=filterById(events["modules"], this.id);
//     test=filterById(events["modules"], this.id);
//     alert(test.module.name);
//     e.stopPropagation();
// })

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

const modal = new bootstrap.Modal(document.getElementById("viewModuleModal"));
var clicked = 0;
var clickedChild=0;

htmx.on("htmx:afterSwap", (e) => {
    if(e.detail.target.id == "modalBody") {
        modal.show();
    }
})

htmx.on("htmx:beforeSwap", (e) => {
    if (e.detail.target.id == "modalBody" && !e.detail.xhr.response){
        modal.hide();
        e.detail.shouldSwap = false;
    }
})