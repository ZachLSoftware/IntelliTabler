const modal = new bootstrap.Modal(document.getElementById("addFormModal"));
var cData ={};
var activePage;
var classToggle=new Set();
var currentClass;



$(document).on("htmx:afterSettle", "#displayChild, #mainContent", (e) =>{
    if(e.detail.pathInfo.requestPath.split('/')[1]=="getModules" || e.detail.pathInfo.requestPath.split('/')[1]=="preferences"){
        if(e.detail.requestConfig.elt.id!="displayChild" && e.detail.requestConfig.elt.id!="preferenceChangeHandler"){
            classToggle= new Set();
        }
        classToggle.forEach(key => {
            var id=key.id.split("Toggle")[0];
            $(key).attr('aria-expanded','true');
            $(`#table${id}`).addClass("show");
            $(`#${id}Icon`).addClass("expand");
        });
    }

});

htmx.on("htmx:afterSwap", (e) => {
    enableTooltips();
    if(e.detail.target.id=="displayChild"){
        $('#displayChild').collapse('show');
        htmx.config.defaultSwapDelay=0;
    }
    if(e.detail.target.id=="sidebarBody"){
        $("#offsetToggle").collapse('show');
        htmx.config.defaultSwapDelay=0;
    }
    if(e.detail.target.id=="mainContent"){
        $('#offcanvasSidebar').offcanvas('hide');
        // $('#mainContent').collapse('show');
        // htmx.config.defaultSwapDelay=0;
    }
    if(e.detail.target.id=="listObjects"){
        let pWidth = 0;
        listSidebar= document.getElementById("listObjectsDiv")
        
        const tempObserver = new ResizeObserver(entries => {
          for (const entry of entries) {
            const width = entry.borderBoxSize?.[0].inlineSize;
            if (typeof width === 'number' && width !== pWidth) {
              pWidth = width;
              $("#displayChild").css("margin-left", width+'px');
            }
          }
        });
        
        tempObserver.observe(listSidebar);
    }

    //AfterSwap for Modal Handeler
    if(e.detail.target.id == "addForm") {
        path=e.detail.pathInfo.requestPath.split('/')[1];
        if(path=="addPreferences" || path=="assignTeacherCombing"){
            setGroupChoice();
        }
        //Enables Tooltips
        enableTooltips();

        modal.show();
    }
    
})

function enableTooltips(){
    $(".tooltip").remove()
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
}


htmx.on("htmx:beforeSwap", (e) => {
    $('#progressLoaderTitle').fadeOut(250, function() {$('#progressLoaderTitle').remove();});
    $('#generatingAnimation').fadeOut(250, function() {$('#generatingAnimation').remove(); $('#mainContent').fadeIn(250);});
    if(e.detail.target.id=="displayChild" && !$(e.detail.target).hasClass('htmx-request') && e.detail.requestConfig.verb!="delete"){
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
    if(e.detail.target.id=="sidebarBody"){
        $("#mainContent").html("");
    }

    //Handles Modal hiding
    if (e.detail.target.id == "addForm" && !e.detail.xhr.response || e.detail.xhr.response==204){
        modal.hide();
        e.detail.shouldSwap = false;
    }
    

    if(cData.calendarDiv && e.target.id=="mainContent"){
        cleanupCalendar();
    }
    if(cData.combing && e.target.id=="mainContent"){
        cleanupCombing();
    }
});

htmx.on('htmx:beforeSend', (e) => {
    if($(e.detail.requestConfig.elt).hasClass("sidebar-link")){
        if($('#progressLoaderTitle').length < 1){
            $("#mainContent").hide();
            html=`<div id="progressLoaderTitle"></div>
            <div id="generatingAnimation"></div>`;
            $("body").prepend(html);
            $('#progressLoaderTitle').html("<h1>Loading...</h1>");
            $('#generatingAnimation').addClass("progressLoader");
        }
    }
    if(($(e.target).hasClass('yearItem'))){
        $("#departmentSelect").text($(e.target).closest('.depDropDown').find('.depItem').text().split(" ").slice(0, -1).join(" ")+" " +$(e.target).text());
    }
    if($(e.target).hasClass('childButtons')){
        if($(e.target).hasClass('moduleButtons')){
            $("#displayChild").attr("hx-get", "/getModules/"+e.target.id.split('Button')[0]+"/"+currentTimetable);

        }else{
            $("#displayChild").attr("hx-get", "/getTeacher/"+e.target.id.split('Button')[0]+"/"+currentTimetable);
        }
        htmx.process(htmx.find("#displayChild"));
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
}
function cleanupCombing(){
    $(document).off("modUpdate");
    
    $(document).off("unassignSuccess");
    
    delete dataModal;
    for(var k in cData){
        delete cData[k];
    }
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

// $(document).on('departmentChange', function(){
//     location.reload();
// })

function getClicked(){
    return clicked;
}

function getChild(){
    return clickedChild;
}

$(document).on("click", ".sidebar-link", function(){
    sidebarActiveLine(this);
});

$(document).on("click", ".list-link", function(){
    listActiveLine(this);
});


function sidebarActiveLine(el){
    activePage=el.id;
    $(".sidebar-link").parent().removeClass("border-bottom");
    $(el).parent().addClass("border-bottom");
}

function listActiveLine(el){
    $(".list-link").parent().removeClass("border-bottom");
    $(el).parent().addClass("border-bottom");
}

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

$(document).on('click', '#teacherInfoBtnGroup button', function(){
    $("#teacherInfoCont .collapse").collapse('hide');
})

$(document).on('teacherDeleted moduleParentDeleted', function(e){
    $("#displayChild").html('');
});

$(document).on("click", ".rotateLink", function(){
    $(this).children("i").toggleClass("expand"); 
});

$(document).on("change", "#parentChoice", function(){
    setGroupChoice();
    
})

$(document).on("change", "#groupChoice", function(){
    setModuleChoice();

})

function setGroupChoice(){
    
    if($("#parentChoice").val()!="None"){
        if(activePage=="combing"){
            var url = '/getGroups/' + $("#parentChoice").val() +'/True';
        }else{
            var url = '/getGroups/' + $("#parentChoice").val();
        }
        $.get(url, function(data){
            $('#groupChoice').empty()
            var options=''
            data.choices.forEach(element => {
                options+= '<option value="' + element[0] +'">' + element[1] +'</option>';
            });
            $('#groupChoice').html(options);
            $('#groupChoice').prop('disabled',false)

            setModuleChoice();
        })
    }else{
        $("#formSubmitBtn").prop('disabled', true)
    }
}
function setModuleChoice(){
    if(activePage=="combing"){
        var url='/getModulesJson/' + $('#groupChoice').val()+"/True";
    }else {
        var url = '/getModulesJson/' + $('#groupChoice').val();
    }
    $.get(url, function(data){
        $('#moduleChoice').empty()
        var options=''
        data.choices.forEach(element => {
            options+= '<option value="' + element[0] +'">' + element[1] +'</option>';
        });
        $('#moduleChoice').html(options);
        $('#moduleChoice').prop('disabled',false)
    })
}

$('#confirmGenerate').click(function(){
    html=`<div id="progressLoaderTitle"></div>
    <div id="generatingAnimation"></div>`;
    $("body").prepend(html);
    $('#progressLoaderTitle').html("<h1>Generating Timetable...</h1>");
    $('#generatingAnimation').addClass("progressLoader");
    $('#confirmModal').modal('hide');
})

$(document).on("sidebarLoaded", function(e){
    url='timetableLanding/'+e.detail.value
    htmx.ajax('GET', url, '#mainContent');
    activePage="timetableLanding"
})

$(document).on("departmentDeleted", function(){
    location.reload();
});

$(document).on("click", ".teacherLanding", function(){
    var timetableId=$(this).attr('timetableId')
    var teacherId=$(this).attr('teacherId')
    htmx.ajax('GET', `/getSidebar/teacher/${timetableId}`, "#mainContent").then(() => {
        htmx.ajax('GET', `/getTeacher/${teacherId}/${timetableId}`, "#displayChild").then(() => {listActiveLine($(`#${teacherId}Button`))});
    });
    sidebarActiveLine($('#teacher'))
})

$(document).on("click", ".classLanding", function(){
    var timetableId=$(this).attr('timetableId')
    var classId=$(this).attr('classId')
    htmx.ajax('GET', `/getSidebar/moduleParent/${timetableId}`, "#mainContent").then(() => {
        htmx.ajax('GET', `/getModules/${classId}/${timetableId}`, "#displayChild").then(() => {listActiveLine($(`#${classId}Button`))});
    });
    sidebarActiveLine($('#class'))
})

$(document).on("timetableDeleted timetableAdded", function(e){
        url="/displayDashboardContent/"+e.detail.value;
        htmx.ajax('GET',url, "#sidebarBody")
})

$(document).on("departmentAdded yearAdded", function(e){
    url="/displayDashboardContent/"+e.detail.tableId;
    htmx.ajax('GET',url, "#sidebarBody");
    $("#departmentSelect").text(e.detail.departmentTitle)
})
$(document).on("departmentChanged", function(e){
    var name = e.detail.departmentName;
    var current =$("#departmentSelect").text().split(" ");
    var year = current[current.length-1];
    $("#departmentSelect").text(name + " " + year);
    $(`#${e.detail.depId}ddbtn`).text(name+" \u00bb");
    $("#departmentInfo")[0].click();
});

htmx.on("htmx:responseError", function(e) {
    var error = JSON.parse(e.detail.xhr.response);
    var errorMessage = error.error;
    var html= `<div class="alert alert-danger alert-dismissible" role="alert">
    <button class="close btn" data-bs-dismiss="alert" aria-label="Close">
      <i class="fa-regular fa-circle-xmark fa-beat fa-xl"></i>
    </button>
    ${errorMessage}
    </div>`
    $('#messageWrapper').append(html)
});

$(document).on("successWithMessage", function(e) {
    var message = e.detail.value;
    var html= `<div class="alert alert-success alert-dismissible" role="alert">
    <button class="close btn" data-bs-dismiss="alert" aria-label="Close">
      <i class="fa-regular fa-circle-xmark fa-beat fa-xl text-dark"></i>
    </button>
    ${message}
    </div>`
    $('#messageWrapper').append(html)
});

$(document).on("asyncResults", function(e) {
    console.log(timetable);
    console.log(activePage);
    if(activePage=="timetableLanding" && e.detail.timetableId==timetable){
        url='timetableLanding/'+ timetable
        htmx.ajax('GET', url, '#mainContent');
    }
    var message = e.detail.resultMsg;
    var html= `<div class="alert alert-${e.detail.result} alert-dismissible" role="alert">
    <button class="close btn" data-bs-dismiss="alert" aria-label="Close">
      <i class="fa-regular fa-circle-xmark fa-beat fa-xl text-dark"></i>
    </button>
    <a class="messageLink" id="popUp${e.detail.timetableId}" hx-get="/displayDashboardContent/${e.detail.timetableId}" hx-target="#sidebarBody">
    ${message}
    </a>
    </div>`
    $('#messageWrapper').append(html);
    htmx.process(htmx.find(`#popUp${e.detail.timetableId}`));
    $(`#taskId-${e.detail.id}`).remove();
    enableButtons();
});

$(document).on("warningWithMessage", function(e) {
    var message = e.detail.value;
    var html= `<div class="alert alert-warning alert-dismissible" role="alert">
    <button class="close btn" data-bs-dismiss="alert" aria-label="Close">
      <i class="fa-regular fa-circle-xmark fa-beat fa-xl text-dark"></i>
    </button>
    ${message}
    </div>`
    $('#messageWrapper').append(html)
});

$(document).on("taskStarted", function(e) {
    var html = `<div id="taskId-${e.detail.value}" hx-get="/taskStatus/${e.detail.value}" hx-trigger="every 5s" hx-target="this"></div>`
    $(body).append(html);
    htmx.process(htmx.find(`#taskId-${e.detail.value}`));
});

$(document).on("change", "input[type='checkbox']", function(){
    // Enable all checkboxes first
    $("input[type='checkbox']").prop('disabled', false);

    // Check Class checkbox
    if ($('#classTemplateCheck').prop('checked')) {
        $("#scheduleTemplateCheck, #preferenceTemplateCheck, #assignTemplateCheck").prop('disabled', true);
    }
    
    // Check Teacher checkbox
    if ($('#teacherTemplateCheck').prop('checked')) {
        $("#preferenceTemplateCheck, #assignTemplateCheck").prop('disabled', true);
    }
    
    // Check Schedule checkbox
    if ($('#scheduleTemplateCheck').prop('checked')) {
        $("#classTemplateCheck").prop('disabled', true);
    }
    
    // Check Preference or Assign checkbox
    if ($('#preferenceTemplateCheck').prop('checked') || $('#assignTemplateCheck').prop('checked')) {
        $("#classTemplateCheck, #teacherTemplateCheck").prop('disabled', true);
    }
});

$(document).on("click", ".classCard", function(){
    if($(this).hasClass("collapsed")){
        classToggle.delete(this);
    }
    else{
        classToggle.add(this);
    }
});

$(document).on("click", ".classHeader", function(){
    target=$(this).attr("data-target");
    $(target).toggleClass("hideClass");
});

$(document).ready(function(){
    if(timetable){
        url="/displayDashboardContent/"+timetable;
        htmx.ajax('GET',url, "#sidebarBody")
        $("#departmentSelect").text(departmentTitle)
    }
    $("#timetableLoad").remove();
})

$(document).on("click","#verifyTimetableBtn", function(e){
    html=`<div id="progressLoaderTitle"></div>
    <div id="generatingAnimation"></div>`;
    $("body").prepend(html);
    $('#progressLoaderTitle').html("<h1>Verifying Assignments...</h1>");
    $('#generatingAnimation').addClass("progressLoader");
    $('#confirmModal').modal('hide');

});

function disableButtons(){
    $(".sidebar-link, .landingLink").not($("#timetableLanding")).addClass('disabled')
}
function enableButtons(){
    $(".sidebar-link, .landingLink").not($("#timetableLanding")).removeClass('disabled')
}