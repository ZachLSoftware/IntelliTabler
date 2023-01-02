$('.form-check-input').prop('checked', false)

for (const period of list){
    let id='#'+period
    $('#'+period).prop('checked', true);
    $('#cell-'+period).addClass('bg-success');
}

getHours();

$('.form-check-input').change(function(){
    if(this.checked){
        $('#cell-'+this.id).addClass('bg-success')
    }else{
        $('#cell-'+this.id).removeClass('bg-success')
    }
    getHours();
});

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
    const remainingHours = totalHours-totalChecked;
    $('#totalHours').text(remainingHours);
    if(remainingHours<0){
        $('#totalHours').addClass('text-danger');
    }else{
        $('#totalHours').removeClass('text-danger');
    }
}