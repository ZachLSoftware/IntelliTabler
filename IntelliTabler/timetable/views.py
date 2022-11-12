from django.shortcuts import render
from .forms import *
from .models import *
from django.shortcuts import get_object_or_404, render, redirect

# Create your views here.
def addDepartment(request):
    if request.method == "POST":
        departmentform = DepartmentForm(request.POST, request.FILES)
        formatform = FormatForm(request.POST, request.FILES)
        if departmentform.is_valid() and formatform.is_valid:
            newdepartment=departmentform.save(commit=False)
            #newdepartment.user=1
            new_format = formatform.save(commit=False)
            new_format.department=newdepartment
            newdepartment.save()
            new_format.save()
            return redirect('/')
    departmentform=DepartmentForm()
    formatform=FormatForm()
    context={
        "departmentform": departmentform,
        "formatform": formatform
    }
    return render(request, 'departmentForm.html',context)