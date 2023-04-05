$('#id_username').keyup(function(){
    var re = /^[\w.@+-]+$/;
    var username = $('#id_username').val()
    if(re.test(username)){
        $('#userHelp').addClass('text-success')
        $('#userHelp').removeClass('text-warning')
    }else{
        $('#userHelp').removeClass('text-success')
        $('#userHelp').addClass('text-warning')
    }
});


$('#id_password1').keyup(function(){
    if($('#id_password1').val().length>=8){
        $('#charLength').addClass('text-success')
    }else{
        $('#charLength').removeClass('text-success')
    }
    if($.isNumeric($('#id_password1').val())){
        $('#numCheck').removeClass('text-success')
        if($('#id_password1').val().length>=8){
            $('#numCheck').addClass('text-danger')
        }else{
            $('#numCheck').addClass('text-warning')
        }
    }else{
        if($('#id_password1').val().length>=1){
            $('#numCheck').removeClass()
            $('#numCheck').addClass('text-success')
        }else{
            $('#numCheck').removeClass()
        }
    }
});