

$(document).on("click", "button", function(){
    if($(this).hasClass("parentButtons")){
        $(".parentButtons").removeClass("active");
        $("#displayChild").html("");
        $("#childColumn").addClass("border-end border-3");
    }else if($(this).hasClass("childButtons")){
        $(".childButtons").removeClass("active");
    }
    else{
        $("button").not(".parentButtons").not(".childButtons").removeClass("active");
    }
    
    $(this).addClass("active");
})


$(".depButton").click(function(){
    $(".depButton").removeClass("active")
    $(this).addClass("active")
    $("#listObjects").html("")
    $("#displayChild").html("")
})

htmx.on("htmx:afterSwap", (e) => {
    if(e.detail.target.id=="displayChild"){
        $('#displayChild').collapse('show');
        htmx.config.defaultSwapDelay=0;
    }
    if(e.detail.target.id=="offCanvasContent"){
        $("#offsetToggle").collapse('show');
        htmx.config.defaultSwapDelay=0;
    }
    if(e.detail.target.id=="mainContent"){
        $('#offcanvasSidebar').offcanvas('hide');
    }
})
htmx.on("htmx:beforeSwap", (e) => {
    if(e.detail.target.id=="displayChild"){
        $('#displayChild').collapse('hide');
        htmx.config.defaultSwapDelay=500;
    }
//     console.log(e.detail.target.id);
//     if(e.detail.target.id=="yearSelectList"){
//         $("#yearSelect").removeClass('disabled');
//     }

//     if(e.detail.target.id=="mainContent"){
//         if($("#mainContent").hasClass('show')){
//             htmx.config.defaultSwapDelay=500;
//             }
       $("#mainContent").collapse('hide');


//     }
    // let done = false
    // let check = setInterval(function(){
    //     console.log("checking");
    //     if(!$("#mainContent").hasClass('collapsing')){
    //         done=true;
    //         clearInterval(check);
    //         console.log(check);
    // }
    // });
})

htmx.on('htmx:beforeSend', (e) => {
    if(($(e.target).hasClass('yearItem'))){
        $("#departmentSelect").text($(e.target).closest('.depDropDown').find('.depItem').text().split(" ")[0]+" " +$(e.target).text());
    }
});