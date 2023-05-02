//Creates the Availability form events to allow for quick checking.
function setupAvailabilityForm(){
    //Set all checkboxes to false
    $('.form-check-input').prop('checked', false)
    
    //Loop through list and check existing classes
    for (const period of list){
        $('#'+period).prop('checked', true);
        $('#'+period).parent().parent().addClass('bg-success');
    }

    //Checks if all boxes for the day are checked, checking the top box.
    $(".fullDayCheck").each(function(){
        if($(`[id^=${this.id}]:checked`).not(this).length==$(`[id^=${this.id}]`).not(this).length){
            $(this).prop("checked", true);
        }
    });

    //Prevents the click bubbling further up the DOM
    $('.form-check-input').on('click', function(e){
        e.stopPropagation();
    });

    //Update background color. Check if all buttons are checked for the day.
    $('.form-check-input').change(function(){
        //Add background color. Check if this is makes all periods in the day checked.
        var dayCheck=this.id.split("-")[0]+"-"+this.id.split("-")[1]
        if(this.checked){
            $('#cell-'+this.id).addClass('bg-success')
            if($(`[id^=${dayCheck}]:checked`).not(`#${dayCheck}`).length==$(`[id^=${dayCheck}]`).not(`#${dayCheck}`).length){
                $(`#${dayCheck}`).prop("checked", true);
            }
        }else{
            //Remove background, uncheck daycheck
            $('#cell-'+this.id).removeClass('bg-success');
            $(`#${dayCheck}`).prop("checked", false);
        }

    });

    //Allows for clicking the whole cell to check the box.
    $('.table-cell').click(function(e){
        let id = '#'+ $(this).attr('id').split("cell-")[1];
        $(id).click();
        e.stopPropagation();
    });

    //Checks all boxes
    $('#selectAll').click(function(){
        $('.form-check-input').prop('checked', true);
        $('.table-cell').addClass('bg-success');
    });

    //Clears all boxes
    $('#clearSelect').click(function(){
        $('.form-check-input').prop('checked', false);
        $('.table-cell').removeClass('bg-success');
    });

    //Shows the availability form now.
    $("#availability").collapse('show');

    //On save, collapse and clear html, clear listener
    $(document).on("availabilitySaved", function(e){
        $('#availability').collapse('hide');
        $('#availability').html('');
        $(document).off("availabilitySaved")
    })

    //Check or uncheck all boxes for the day.
    $(".fullDayCheck").change(function(e){
        if($(this).prop("checked")){
            $(`[id^=${this.id}]`).not(this).prop('checked',true);
            $(`[id^=${this.id}]`).not(this).closest('td').addClass('bg-success');
        }else{
            $(`[id^=${this.id}]`).not(this).prop('checked',false)
            $(`[id^=${this.id}]`).not(this).closest('td').removeClass('bg-success');
        }
    });
}
