//Create calendar object
function createCalendar(id){
    dataModal = new bootstrap.Modal(document.getElementById("viewDataModal")); //Set data modal
    cData.calendarDiv=id; //Get calendar div location
    var days=['Mon', 'Tues', 'Wed', 'Thurs', 'Fri'] //create days array
    
    //Create a seperate div for each calendar week
    for(let week=1; week<=cData.weeks; week++){
        $(cData.calendarDiv).append(`<div id="calendarWeek-${week}" class="calendars" style="height: auto"></div>`)
    }

    //Hide all calendars, set 1st week as active and show.
    $(".calendars").hide()
    $("#calendarWeek-1").addClass("activeCalendar");
    $("#calendarWeek-1").show()
    setActive();

    //For each week, build the structure of the calendar.
    $(".calendars").each(function(index){
        //Get week
        week=this.id.split('-')[1]

        //Append the header column for periods
        $(this).append(`<div id="periodColumn-${week}" class="dayHeader periodColumn"><div class="calendarHeader"><h3>Period</h3></div></div>`)

        //Loop through days
        days.forEach((day) =>{
            //Append the column header for each day.
            $(this).append(`<div id="${day}Header-${week}" class="dayHeader"><div class="calendarHeader"><h3>${day}</h3></div></div>`);

            //Loop through periods for each day and append a cell.
            for(let period=1; period<=cData.periods; period++){
                $(`#${day}Header-${week}`).append(`<div id="${day}-${period}-${week}" class="dayCell"></div>`);

                //If day is friday, set end column
                if(day=="Fri"){$(`#${day}Header-${week}`).addClass("endColumn")}

                //Set droppable listener
                $(`#${day}-${period}-${week}`).droppable({accept:".event", drop: function(e, ui){        
                    $(ui.draggable).appendTo(this);
                    $(ui.draggable).css({'top' : 0, 'left' : 0})
                    p=this.id.split('-')
                    var element = htmx.ajax('POST', `/calendarPeriodDrop/${p[0]}-${p[1]}/${p[2]}/${ui.draggable[0].id}`); //Set drop ajax function
                    }
                });
            }
        });

        //Create each period row
        for(let period=1; period<=cData.periods; period++){
            $(`#periodColumn-${week}`).append(`<div class="pRow">${period}</div>`);
        }

    });
    //Create CSS Grid
    $(".dayHeader").css("grid-template-rows", `1fr repeat(${cData.periods}, 3fr`);

    //Add all calendar events from cData
    cData.events["modules"].forEach((mod) => addCalEvent(mod));

    //process htmx
    refreshListeners();

    //Create cell listeners to get form when clicked.
    $(".dayCell").on("click", function(e){
        if(this!=e.target){
            return false;
        }
        var id=this.id.split('-');
        if(!cData.teacher){
        
            htmx.ajax('GET', `/addModuleCalendar/${id[0]}-${id[1]}/${id[2]}/${cData.timetable}`, '#addForm');
        }
    });

    /*
    Handels the next and previous arrow animations and setting active calendar.
    */
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
    
};

//Function to add a new event to the calendar.
function addCalEvent(mod){
        //Create object and append to the correct calendar cell.
        $(`#${mod.period.name}-${mod.period.week}`).append(`<button id="${mod.id}" hx-get="/getModules/${mod.groupid}?calendar=1" hx-target="#modalBody" class="event btn m-1 ${mod.parent.id}">${mod.name}</button>`);
        //Set element background and text color.
        $(`#${mod.id}`).css('background-color', mod.parent.color);
        $(`#${mod.id}`).css('color',getTextColor(mod.parent.color));

        //Set draggable listener if not in teacher view
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

//Used to filter json objects by id. Depricated.
function filterById(jsonObject, id) {
    return jsonObject.filter(function(jsonObject) {
        return (jsonObject['id'] == id);})[0];
};

//Sets the active calendar, disabling arrows if at beginning or end.        
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

//Refreshes htmx listeners
function refreshListeners(){
    htmx.process(htmx.find(cData.calendarDiv));   
}

//Prevents clicks propogating
$(cData.calendarDiv).on("click", ".event", function(e){
    clicked=this.id;
    e.stopPropagation();
});

//Listener for when an event is added.
$(document).on("addCalendarEvent", function(e){
    e.detail.modules.forEach((mod) => addCalEvent(mod));
    refreshListeners();
});

//Listener for when a period is updated.
$(document).on("periodUpdate", function(e){
    e.detail.modules.forEach((mod) => {
        $(`#${mod.id}`).remove() //Removes existing elements before re-adding them
        addCalEvent(mod);
    });
    refreshListeners(); //Process new htmx elements
});

//Updates element colors when a parent color is changed.
$(document).on("updateColor",function(e){
    $(`.${e.detail.parentId}`).css("background-color", e.detail.color);
    $(`.${e.detail.parentId}`).css("color", getTextColor(e.detail.color));
});