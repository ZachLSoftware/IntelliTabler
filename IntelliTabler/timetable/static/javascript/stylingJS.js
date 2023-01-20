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
