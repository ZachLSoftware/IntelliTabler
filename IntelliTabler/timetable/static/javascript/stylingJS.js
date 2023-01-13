$(document).on("click", "button", function(){
    if($(this).hasClass("departmentButtons")){
        $("button").removeClass("active");
        $("#displayTeacher").html("");
        $("#teacherColumn").addClass("border-end border-3");
    }else if($(this).hasClass("teacherButtons")){
        $("button").not(".departmentButtons").removeClass("active");
    }
    else{
        $("button").not(".departmentButtons").not(".teacherButtons").removeClass("active");
    }
    
    $(this).addClass("active");
})

