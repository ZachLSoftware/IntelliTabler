var i=0;
for (const period of modulePeriods){
    let id='#'+ period
    $('#'+period).val(moduleNames[i])
    i++;
}