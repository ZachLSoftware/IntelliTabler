const modal = new bootstrap.Modal(document.getElementById("addFormModal")); //Bootstrap Modal
var cData ={}; //Calendar and combing chart data structure
var activePage; //Current page selection
var classToggle=new Set(); //Set used to track expanded sections
//var currentClass;

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

/*
Listener to handle afterSettle of htmx swap. 
Specifically used in teacher and class pages
to re-expand sections after refresh.
*/
$(document).on("htmx:afterSettle", "#displayChild, #mainContent", (e) =>{

    //Check if the request path is for getModules or Prerences
    if(e.detail.pathInfo.requestPath.split('/')[1]=="getModules" || e.detail.pathInfo.requestPath.split('/')[1]=="preferences"){

        //If the page is switching, clear classToggle
        if(e.detail.requestConfig.elt.id!="displayChild" && e.detail.requestConfig.elt.id!="preferenceChangeHandler"){
            classToggle= new Set();
        }

        //For each element that is expanded in class toggle, get id and expand.
        classToggle.forEach(key => {
            var id=key.id.split("Toggle")[0];
            $(key).attr('aria-expanded','true');
            $(`#table${id}`).addClass("show");
            $(`#${id}Icon`).addClass("expand");
        });
    }
});

/*
After swapping in DOM elements. 
Used to enable tooltips, handle showing objects,
Resizing elemnts and more.
*/
htmx.on("htmx:afterSwap", (e) => {

    //Enable any tooltips on the page.
    enableTooltips();

    //If the target is displaying child information
    //Show the element and reset the swap delay to 0
    if(e.detail.target.id=="displayChild"){
        $('#displayChild').collapse('show');
        htmx.config.defaultSwapDelay=0;
    }

    //If inserting the listObjects div, get the size of the 
    //current sidebar and set width of display child.
    if(e.detail.target.id=="listObjects"){
        let pWidth = 0;
        listSidebar= document.getElementById("listObjectsDiv")
        
        //Create an observer to handle resizing of displayChild div
        const tempObserver = new ResizeObserver(entries => {
          for (const entry of entries) {
            const width = entry.borderBoxSize?.[0].inlineSize;
            if (typeof width === 'number' && width !== pWidth) {
              pWidth = width;
              $("#displayChild").css("margin-left", width+'px');
            }
          }
        });
        
        //Set Observer.
        tempObserver.observe(listSidebar);
    }

    //Remove edit button for module details if in the modalBody and in combing.
    //Add hx-get attribute and process changes
    if(e.detail.target.id == "modalBody" && activePage=="combing") {
        $('.editBtnCol').remove();
        $("#modalBody").attr("hx-get",e.detail.pathInfo.requestPath);
        htmx.process(htmx.find("#modalBody"));
        dataModal.show();
    }

    //Remove edit button on calendar modal if in teacher view
    if(e.detail.target.id == "modalBody") {
        if (cData.teacher){
            $(".editBtnCol").remove()
        }
        dataModal.show();
    }

    //AfterSwap for Modal Handeler
    if(e.detail.target.id == "addForm") {
        path=e.detail.pathInfo.requestPath.split('/')[1];

        //Add group choices for dropdowns.
        if(path=="addPreferences" || path=="assignTeacherCombing"){
            setGroupChoice();
        }
        modal.show();
    }
    
});

/*
Handle content before being swapped by htmx.
Includes removing loading animation, adding swap delays,
hiding elements, etc.
*/
htmx.on("htmx:beforeSwap", (e) => {

    //Remove the loading animation ready for swapping, fade in maincontent
    $('#progressLoaderTitle').fadeOut(250, function() {$('#progressLoaderTitle').remove();});
    $('#generatingAnimation').fadeOut(250, function() {$('#generatingAnimation').remove(); $('#mainContent').fadeIn(250);});

    //If displaying child info, delay swap so collapse can complete cleanly.
    if(e.detail.target.id=="displayChild" && !$(e.detail.target).hasClass('htmx-request') && e.detail.requestConfig.verb!="delete"){
        if($('#displayChild').hasClass('show')){
            htmx.config.defaultSwapDelay=500;
        }
        $('#displayChild').collapse('hide');
    }

    //If swapping the sidebarbody, clear maincontent
    if(e.detail.target.id=="sidebarBody"){
        $("#mainContent").html("");
    }

    //Handles Modal hiding
    if (e.detail.target.id == "addForm" && !e.detail.xhr.response || e.detail.xhr.response==204){
        modal.hide();
        e.detail.shouldSwap = false;
    }
    if (e.detail.target.id == "modalBody" && !e.detail.xhr.response){
        dataModal.hide();
        e.detail.shouldSwap = false;
    }
    
    //Cleanup listeners and cData if page swap after combing or calendar
    if(cData.calendarDiv && e.target.id=="mainContent"){
        cleanupCalendar();
    }
    if(cData.combing && e.target.id=="mainContent"){
        cleanupCombing();
    }
});

/*
Handles content before sending and htmx request.
Includes adding a loading animation, adding hx elements,
and setting dropdown texts
*/
htmx.on('htmx:beforeSend', (e) => {
    //If clicked on a sidebar link, append loading animation
    if($(e.detail.requestConfig.elt).hasClass("sidebar-link")){

        //Confirm another loader hasn't already been added.
        if($('#progressLoaderTitle').length < 1){
            $("#mainContent").hide();
            html=`<div id="progressLoaderTitle"></div>
            <div id="generatingAnimation"></div>`;
            $("body").prepend(html);
            $('#progressLoaderTitle').html("<h1>Loading...</h1>");
            $('#generatingAnimation').addClass("progressLoader");
        }
    }

    //If clicked on a year, set the department select to the department + year
    if(($(e.target).hasClass('yearItem'))){
        $("#departmentSelect").text($(e.target).closest('.depDropDown').find('.depItem').text().split(" ").slice(0, -1).join(" ")+" " +$(e.target).text());
    }

    //If creating child buttons, add the proper hx-get attribute and process.
    if($(e.target).hasClass('childButtons')){
        if($(e.target).hasClass('ClassButtons')){
            $("#displayChild").attr("hx-get", "/getModules/"+e.target.id.split('Button')[0]+"/"+currentTimetable);

        }else{
            $("#displayChild").attr("hx-get", "/getTeacher/"+e.target.id.split('Button')[0]+"/"+currentTimetable);
        }
        htmx.process(htmx.find("#displayChild"));
    }
});

//Enable bootstrap tooltips for the page
function enableTooltips(){
    //Remove any existing tooltips before re-adding.
    $(".tooltip").remove()

    //Find all tooltips and set to trigger.
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
};


/*
Cleanup functions for calendar and combing.
Remove any universal listeners to prevent
multiple listeners.
Clear cData.
*/
function cleanupCalendar(){
    $(document).off("addEvent");
    
    $(document).off("periodUpdate");
    
    $(document).off("updateColor");
    delete dataModal;
    $(cData.calendarDiv).off();
    for(var k in cData){
        delete cData[k];
    }
};
function cleanupCombing(){
    $(document).off("modUpdate");
    
    $(document).off("unassignSuccess");

    $(document).off("click", ".removeMod");
    
    $(document).off("updateColor");
    
    delete dataModal;
    for(var k in cData){
        delete cData[k];
    }
};

//Clears modal html
htmx.on("hidden.bs.modal", () => {
    $("#addForm").html("");
});

//If sidebar link clicked, add active line
$(document).on("click", ".sidebar-link", function(){
    sidebarActiveLine(this);
});

//If list link, set list link active line
$(document).on("click", ".list-link", function(){
    listActiveLine(this);
});

//Adds a line to active link
function sidebarActiveLine(el){
    //Set active page variable
    activePage=el.id;
    
    //Remove line of other elements, add to current active page
    $(".sidebar-link").parent().removeClass("border-bottom");
    $(el).parent().addClass("border-bottom");
};

//Add line to active list link
function listActiveLine(el){
    $(".list-link").parent().removeClass("border-bottom");
    $(el).parent().addClass("border-bottom");
}

//Get text color based on brightness of background color.
function getTextColor(color){

    //Convert hex into RGB
    rgb=color.split('#')[1].match(/.{1,2}/g);
    r=parseInt(rgb[0], 16);
    g=parseInt(rgb[1], 16);
    b=parseInt(rgb[2], 16);
    //Test brightness and return black or white text
    if ((r*0.299 + g*0.587 + b*0.114) > 150) {
        return '#000000'
     }else{
        return '#ffffff';
     }
};

//Collapse content when a top level button is pressed in teachers.
$(document).on('click', '#teacherInfoBtnGroup button', function(){
    $("#teacherInfoCont .collapse").collapse('hide');
});

//Clean displayChild html when object is deleted
$(document).on('teacherDeleted moduleParentDeleted', function(e){
    $("#displayChild").html('');
});

//Handle expand toggle class
$(document).on("click", ".rotateLink", function(){
    $(this).children("i").toggleClass("expand"); 
});

//When a parent choice is changed, update group choice
$(document).on("change", "#parentChoice", function(){
    setGroupChoice();
});

//When a group choice is changed, update module choice
$(document).on("change", "#groupChoice", function(){
    setModuleChoice();
});

/*
Function to dynamically display module choices
on drop down menus. Used to help select modules
in places like the combing chart.
*/
function setGroupChoice(){
    
    //If not none, get groups. Combing requires special grouping.
    if($("#parentChoice").val()!="None"){
        if(activePage=="combing"){
            var url = '/getGroups/' + $("#parentChoice").val() +'/True';
        }else{
            var url = '/getGroups/' + $("#parentChoice").val();
        }

        //Ajax function to get and update choices
        $.get(url, function(data){
            //Clear choices.
            $('#groupChoice').empty()
            var options=''

            //Add choices 
            data.choices.forEach(element => {
                options+= '<option value="' + element[0] +'">' + element[1] +'</option>';
            });
            //Insert options html and enable dropdown
            $('#groupChoice').html(options);
            $('#groupChoice').prop('disabled',false);

            setModuleChoice();
        });
    }else{
        //Disable submit no options available
        $("#formSubmitBtn").prop('disabled', true);
    }
};

/*
Add Modules to drop down based on group
*/
function setModuleChoice(){

    //Get modules in json format from groupchoice value
    if(activePage=="combing"){
        var url='/getModulesJson/' + $('#groupChoice').val()+"/True";
    }else {
        var url = '/getModulesJson/' + $('#groupChoice').val();
    }

    //AJAX get function to add choices
    $.get(url, function(data){
        //Empty dropdown
        $('#moduleChoice').empty()

        //Create html based on data
        var options=''
        data.choices.forEach(element => {
            options+= '<option value="' + element[0] +'">' + element[1] +'</option>';
        });

        //Insert html and enable dropdown.
        $('#moduleChoice').html(options);
        $('#moduleChoice').prop('disabled',false)
    });
};


//Add generating animation when user confirms auto assignment.
$('#confirmGenerate').click(function(){
    html=`<div id="progressLoaderTitle"></div>
    <div id="generatingAnimation"></div>`;
    $("body").prepend(html);
    $('#progressLoaderTitle').html("<h1>Generating Timetable...</h1>");
    $('#generatingAnimation').addClass("progressLoader");
    $('#confirmModal').modal('hide');
});

//Automatically get timetable Landing page when the sidebar
//for a specific timetable is loaded.
$(document).on("sidebarLoaded", function(e){
    url='timetableLanding/'+e.detail.value
    htmx.ajax('GET', url, '#mainContent');
    activePage="timetableLanding"
});

//When a department is deleted, refresh the page.
$(document).on("departmentDeleted", function(){
    location.reload();
});

/*
Handles shortcut link from timetable landing page for a teacher.
Uses htmx to get the teacher sidebar, then the specific teacher.
*/
$(document).on("click", ".teacherLanding", function(){
    var timetableId=$(this).attr('timetableId');
    var teacherId=$(this).attr('teacherId');

    //Get sidebar for teachers, when completed, get teacher info, then set active line.
    htmx.ajax('GET', `/getSidebar/teacher/${timetableId}`, "#mainContent").then(() => {
        htmx.ajax('GET', `/getTeacher/${teacherId}/${timetableId}`, "#displayChild").then(() => {listActiveLine($(`#${teacherId}Button`))});
    });

    //Set the active line
    sidebarActiveLine($('#teacher'));
});

/*
Handles shortcut link from timetable landing page for a class.
Uses htmx to get the class sidebar, then the specific class.
*/
$(document).on("click", ".classLanding", function(){
    var timetableId=$(this).attr('timetableId');
    var classId=$(this).attr('classId');
    htmx.ajax('GET', `/getSidebar/moduleParent/${timetableId}`, "#mainContent").then(() => {
        htmx.ajax('GET', `/getModules/${classId}/${timetableId}`, "#displayChild").then(() => {listActiveLine($(`#${classId}Button`))});
    });
    sidebarActiveLine($('#class'))
})

//When a timetable is deleted or added, refresh dashboard content.
$(document).on("timetableDeleted timetableAdded", function(e){
        url="/displayDashboardContent/"+e.detail.value;
        htmx.ajax('GET',url, "#sidebarBody")
});

//When a department or year are added, refresh dropdowns and get default timetable.
$(document).on("departmentAdded yearAdded", function(e){

    //Refresh sidebar, then get dashboard content for default timetable
    htmx.ajax('GET','/getSidebarDepartments', "#sidebarHeader").then(() => {
        url="/displayDashboardContent/"+e.detail.tableId;
        htmx.ajax('GET',url, "#sidebarBody");
        $("#departmentSelect").text(e.detail.departmentTitle)
    });
});

//Handle department name change.
$(document).on("departmentChanged", function(e){
    var name = e.detail.departmentName;
    var current =$("#departmentSelect").text().split(" ");
    var year = current[current.length-1];
    $("#departmentSelect").text(name + " " + year);
    $(`#${e.detail.depId}ddbtn`).text(name+" \u00bb");
    $("#departmentInfo")[0].click();
});

//Displays an error message at top of page when there is an error message.
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

//Displays a success message when triggered.
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

//Handles the displaying of Asynchonous task results
$(document).on("asyncResults", function(e) {

    //If user is on the timetableLanding page for the task, refresh.
    if(activePage=="timetableLanding" && e.detail.timetableId==timetable){
        url='timetableLanding/'+ timetable
        htmx.ajax('GET', url, '#mainContent');
    }

    //Create pop up with a link to the completed timetable
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

    //Process the hx-get for the popup
    htmx.process(htmx.find(`#popUp${e.detail.timetableId}`));

    //Remove polling div and enable buttons for the timetable.
    $(`#taskId-${e.detail.id}`).remove();
    enableButtons();
});

//Creates a message if warning triggered
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

//Creates a polling div to get task status.
$(document).on("taskStarted", function(e) {
    var html = `<div id="taskId-${e.detail.value}" hx-get="/taskStatus/${e.detail.value}" hx-trigger="every 5s" hx-target="this"></div>`
    $(body).append(html);
    htmx.process(htmx.find(`#taskId-${e.detail.value}`));
});


//Handles excel template selections.
$(document).on("change", ".templateSelectorForm", function(){
    //Enable all checkboxes first
    $(".templateSelectorForm").prop('disabled', false);

    //Check through and disable depending on checked.
    if ($('#classTemplateCheck').prop('checked')) {
        $("#scheduleTemplateCheck, #preferenceTemplateCheck, #assignTemplateCheck").prop('disabled', true);
    }
    if ($('#teacherTemplateCheck').prop('checked')) {
        $("#preferenceTemplateCheck, #assignTemplateCheck").prop('disabled', true);
    }
    if ($('#scheduleTemplateCheck').prop('checked')) {
        $("#classTemplateCheck").prop('disabled', true);
    }
    if ($('#preferenceTemplateCheck').prop('checked') || $('#assignTemplateCheck').prop('checked')) {
        $("#classTemplateCheck, #teacherTemplateCheck").prop('disabled', true);
    }
});

//Tracks expanded cards in teacher and class pages.
$(document).on("click", ".classCard", function(){
    if($(this).hasClass("collapsed")){
        classToggle.delete(this);
    }
    else{
        classToggle.add(this);
    }
});

//Toggles collapse for teacher modules section
$(document).on("click", ".classHeader", function(){
    target=$(this).attr("data-target");
    $(target).toggleClass("hideClass");
});

//Checks if a timetable id has been passed to dashboard base.
//If yes, then load that timetable, then remove the script.
$(document).ready(function(){
    if(timetable){
        url="/displayDashboardContent/"+timetable;
        htmx.ajax('GET',url, "#sidebarBody")
        $("#departmentSelect").text(departmentTitle)
    }
    $("#timetableLoad").remove();
});

//Adds animation for verifying task
$(document).on("click","#verifyTimetableBtn", function(e){
    html=`<div id="progressLoaderTitle"></div>
    <div id="generatingAnimation"></div>`;
    $("body").prepend(html);
    $('#progressLoaderTitle').html("<h1>Verifying Assignments...</h1>");
    $('#generatingAnimation').addClass("progressLoader");
    $('#confirmModal').modal('hide');

});

//Handles enabling and disabling buttons for timetables.
function disableButtons(){
    $(".sidebar-link, .landingLink").not($("#timetableLanding")).addClass('disabled')
}
function enableButtons(){
    $(".sidebar-link, .landingLink").not($("#timetableLanding")).removeClass('disabled')
}