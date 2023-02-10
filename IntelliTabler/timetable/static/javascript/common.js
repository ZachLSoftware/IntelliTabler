const modal = new bootstrap.Modal(document.getElementById("addFormModal"));
const dataModal = new bootstrap.Modal(document.getElementById("viewDataModal"));
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
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

        modal.show();
    }
})


htmx.on("htmx:beforeSwap", (e) => {

    if(e.detail.target.id=="displayChild"){
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
})

htmx.on('htmx:beforeSend', (e) => {
    if(($(e.target).hasClass('yearItem'))){
        $("#departmentSelect").text($(e.target).closest('.depDropDown').find('.depItem').text().split(" ")[0]+" " +$(e.target).text());
        console.log("#offcanvasLabel")
        $("#offcanvasLabel").text($(e.target).closest('.depDropDown').find('.depItem').text().split(" ")[0]+" " +$(e.target).text());
    }
});

htmx.on("hidden.bs.modal", () => {
    $("#addForm").html("");
});

$(document).on("click", ".parentButtons, .childButtons", function(){
    if($(this).hasClass("childButtons")){
        clickedChild=this.id.split('.')[0]
        console.log(clickedChild);
    }else{
        clicked=this.id.split('.')[0];
        console.log(clicked);
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