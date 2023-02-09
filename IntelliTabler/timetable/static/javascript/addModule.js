let totalForms = $("#id_form-TOTAL_FORMS");

let formNum = $('.moduleFormDiv').length;
var tempId = 0;

console.log(currentModulePeriods)

console.log($('#add-form-1'));


$(document).ready(function(){

    let errorId=[];
    for (period in currentModulePeriods){
        let btn = '#add-form-' + currentModulePeriods[period];
        $(btn).click();
        $('#name-'+tempId).val(currentModuleNames[period]);
        if(errors[period]!="None"){
            errorId.push(tempId);
        }
    }

    for (err in errorId){
        addError(errorId[err]);
    }
})

function addError(id){
    let msg=document.createElement('p');
    msg.classList.add('text-danger')
    msg.innerHTML="Module must follow the format 10x5";
    $('#'+id).before(msg);
}



$(".addFormButton").click(function(){
    addForm(this);
});

$(document).on("click", ".deleteFormButton", function(){
    var res = confirm("Delete this module?")
    if(res){
        deleteForm(this);
    }
});

$('#sbmBtn').click(function(){
    $('.moduleNameField').each(function(i, obj){
        if(obj.value==='' && obj.value.length ===0){
            let form=document.getElementById('delete-form-'+obj.id.match(/[0-9]+-[0-9]+/)[0]);
            deleteForm(form);
        }
    })
})

function addForm(e, error){
    //Setup
    let cellNum = parseInt(e.parentElement.id.match(/[0-9]+$/));
    let cellId = "#" + e.parentElement.id;
    var divFormat=document.createElement('div');
    if(formNum===0){
        var newForm = document.createElement('div');
        newForm.classList.add("moduleFormDiv")
        newForm.classList.add("container-fluid")
        newForm.innerHTML=`
        <div class="row">
        <div class="col-md-auto">
        <input type="text" name="form-0-moduleName" placeholder="Enter a Module" class="form-control moduleNameField" id="name-1-1">
        <input type="text" name="form-0-modulePeriod" value="mon-1" id="period-1-1" hidden="True">
        <input type="number" name="form-0-moduleWeek" value="1" hidden="True">
        </div>
        <div class="col-md-auto">
        <button id="delete-form-{{forloop.counter}}" type="button" class="btn btn-sm btn-warning deleteFormButton">Delete</button>
        </div>
        </div>
        </br>
        `
    }else{
        var newForm = $('.moduleFormDiv')[0].cloneNode(true);
    }
    let newFields=newForm.children[0].children[0].children;

    let moduleCount = $(cellId + " .moduleFormDiv").length+1;
    let formCount = formNum-1;
    let newId = cellNum + "-" + moduleCount;
    let newName = "form-" + formNum;
    newFields[0].setAttribute('id', "name-" + newId);
    newFields[0].setAttribute('name', newName + "-moduleName");
    newFields[1].setAttribute('id', "period-" + newId);
    newFields[1].setAttribute('name', newName + "-modulePeriod");
    newFields[2].setAttribute('name', newName + "-moduleWeek");
    newFields[0].value='';
    if(cellNum<26){
        newFields[1].setAttribute('value', periods[cellNum-1]);
        newFields[2].setAttribute('value', 1);
    }else{
        newFields[1].setAttribute('value', periods[cellNum-26]);
        newFields[2].setAttribute('value', 2);
    }
    newForm.children[0].children[1].children[0].setAttribute('id', "delete-form-"+newId);
    newForm.setAttribute('id', newId);
    newForm.setAttribute('name', newName);
    e.parentElement.insertBefore(newForm, e);
    formNum++;
    totalForms.val(formNum);
    tempId =  newId;
}

function deleteForm(item){
    let formId=item.id.match(/[0-9]+-[0-9]+/)[0];
    let formNumber=parseInt($("#name-"+formId).attr('name').match(/[0-9]+/));

    $('.moduleFormDiv').each(function(i, obj){
        let num = parseInt(obj.getAttribute('name').match(/[0-9+$]/))
        if(num>formNumber){
            let newNum=num-1;
            let newName="form-"+newNum;
            let fields=obj.children[0].children[0].children;
            fields[0].setAttribute('name', newName + "-moduleName");
            fields[1].setAttribute('name', newName + "-modulePeriod");
            fields[2].setAttribute('name', newName + "-moduleWeek");
            obj.setAttribute('name', newName);
        }
    })

    $('#'+formId).remove();
    formNum--;
    totalForms.val(formNum);



}