const modal = new bootstrap.Modal(document.getElementById("addFormModal"));
var cData ={};
var activePage;
$(document).on("click", ".childButtons", function(){
    if($(this).hasClass("childButtons")){
        $(".childButtons").removeClass("active");
    }
    else{
        $("button").not(".parentButtons").not(".childButtons").removeClass("active");
    }
    
    $(this).addClass("active");
})

htmx.on("htmx:afterSwap", (e) => {
    if(e.detail.target.id=="displayChild"){
        $('#displayChild').collapse('show');
        htmx.config.defaultSwapDelay=0;
    }
    if(e.detail.target.id=="offcanvasBody"){
        $("#offsetToggle").collapse('show');
        htmx.config.defaultSwapDelay=0;
    }
    if(e.detail.target.id=="mainContent"){
        $('#offcanvasSidebar').offcanvas('hide');
        // $('#mainContent').collapse('show');
        // htmx.config.defaultSwapDelay=0;
    }

    //AfterSwap for Modal Handeler
    if(e.detail.target.id == "addForm") {
        //Enables Tooltips
        enableTooltips();

        modal.show();
    }
})

function enableTooltips(){
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
}


htmx.on("htmx:beforeSwap", (e) => {

    if(e.detail.target.id=="displayChild" && !$(e.detail.target).hasClass('htmx-request')){
        if($('#displayChild').hasClass('show')){
            htmx.config.defaultSwapDelay=500;
        }
        $('#displayChild').collapse('hide');

    }
    // if(e.detail.target.id=="mainContent"){
    //     if($('#mainContent').hasClass('show')){
    //         htmx.config.defaultSwapDelay=500;
    //     }
    //     $("#mainContent").collapse('hide');
    // }
    if(e.detail.target.id=="offcanvasBody"){
        $("#mainContent").html("");
    }

    //Handles Modal hiding
    if (e.detail.target.id == "addForm" && !e.detail.xhr.response){
        modal.hide();
        e.detail.shouldSwap = false;
    }

    if(cData.calendarDiv && e.target.id=="mainContent"){
        cleanupCalendar();
    }
})

htmx.on('htmx:beforeSend', (e) => {
    if(($(e.target).hasClass('yearItem'))){
        $("#departmentSelect").text($(e.target).closest('.depDropDown').find('.depItem').text().split(" ")[0]+" " +$(e.target).text());
        $("#offcanvasLabel").text($(e.target).closest('.depDropDown').find('.depItem').text().split(" ")[0]+" " +$(e.target).text());
    }
    if($(e.target).hasClass('childButtons')){
        if($(e.target).hasClass('moduleButtons')){
            $("#displayChild").attr("hx-get", "/getModules/"+e.target.id.split('.')[0]+"/"+currentTimetable);

        }else{
            $("#displayChild").attr("hx-get", "/getTeacher/"+e.target.id.split('.')[0]+"/"+currentTimetable);
        }
        htmx.process(htmx.find("#displayChild"));
    }
    if($(e.target).hasClass('event')){
        $("#modalBody").attr("hx-get", "/getModules/"+e.target.id+"?calendar=1");
        htmx.process(htmx.find("#modalBody"));
    }
})

function cleanupCalendar(){
    $(document).off("addEvent");
    
    $(document).off("periodUpdate");
    
    $(document).off("updateColor");
    delete dataModal;
    $(cData.calendarDiv).off();
    for(var k in cData){
        delete cData[k];
    }
    console.log(cData);
}

htmx.on("hidden.bs.modal", () => {
    $("#addForm").html("");
});

$(document).on("click", ".parentButtons, .childButtons", function(){
    if($(this).hasClass("childButtons")){
        clickedChild=this.id.split('.')[0]
    }else{
        clicked=this.id.split('.')[0];
    }
    
    });

$(document).on('departmentChange yearChange', function(){
    location.reload();
})

function getClicked(){
    return clicked;
}

function getChild(){
    return clickedChild;
}

$(document).on("click", ".sidebar-link", function(){
    activePage=this.id;
    $(".sidebar-link").parent().removeClass("border-bottom");
    $(this).parent().addClass("border-bottom");
})

let prevWidth = 0;
sidebar= document.getElementById("sidebar")

const sidebarObserver = new ResizeObserver(entries => {
  for (const entry of entries) {
    const width = entry.borderBoxSize?.[0].inlineSize;
    if (typeof width === 'number' && width !== prevWidth) {
      prevWidth = width;
      $("#contentCol").css("margin-left", width+'px');
    }
  }
});

sidebarObserver.observe(sidebar);

function getTextColor(color){
    rgb=color.split('#')[1].match(/.{1,2}/g);
    r=parseInt(rgb[0], 16);
    g=parseInt(rgb[1], 16);
    b=parseInt(rgb[2], 16);
    if ((r*0.299 + g*0.587 + b*0.114) > 150) {
        return '#000000'
     }else{
        return '#ffffff';
     }
}

$(document).on('click', '#infoBtnGroup button', function(){
    $("#teacherInfoCont .collapse").collapse('hide');
})

$(document).on('objectDeleted', function(e){
    $("#displayChild").html('');
});