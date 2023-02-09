$('.form-check-input').prop('checked', false)

for (const period of list){
    $('#'+period).prop('checked', true);
    $('#'+period).parent().parent().addClass('bg-success');
}

getHours();

$('.form-check-input').on('click', function(e){
    e.stopPropagation();
})

$('.form-check-input').change(function(){
    if(this.checked){
        $('#cell-'+this.id).addClass('bg-success')
    }else{
        $('#cell-'+this.id).removeClass('bg-success')
    }

});

$('.table-cell').click(function(e){
    let id = '#'+ $(this).attr('id').split("cell-")[1];
    $(id).click();
    e.stopPropagation();
})

$('#selectAll').click(function(){
    $('.form-check-input').prop('checked', true);
    $('.table-cell').addClass('bg-success');
    getHours();
});

$('#clearSelect').click(function(){
    $('.form-check-input').prop('checked', false);
    $('.table-cell').removeClass('bg-success');
    getHours();
});

function getHours(){
    const totalChecked = $('.form-check-input:checkbox:checked').length;
    const remainingHours = load-totalChecked;
    $('#load').text(remainingHours);
    if(remainingHours<0){
        $('#load').addClass('text-danger');
    }else{
        $('#load').removeClass('text-danger');
    }
}