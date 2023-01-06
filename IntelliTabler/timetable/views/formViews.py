from django.urls import reverse
from django.http import HttpResponse
from ..forms import *
from ..models import *
from django.forms import formset_factory
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
            newdepartment.user=request.user
            newdepartment.save()
            new_format.save()
            return HttpResponse(status=204, headers={'HX-Trigger':'departmentChange'})
    else:
        departmentform=DepartmentForm()
        formatform=FormatForm()
    context={
        "departmentform": departmentform,
        "formatform": formatform
    }
    return render(request, 'forms/departmentForm.html',context)

def addTeacher(request, department, id=0):
    if request.method=="POST":
        Teacher.objects.filter(pk=0).delete()
        teacher, created=Teacher.objects.get_or_create(id=request.POST['id'], user=request.user, department_id=department)
        Teacher.objects.filter(pk=0).delete()
        form = TeacherForm(request.POST, instance=teacher)
        if(form.is_valid()):
            print(teacher)
            newTeacher=form.cleaned_data
            newTeacher["user"]=request.user
            newTeacher["department"]=Department.objects.get(id=department)
            teacher.save()
            #Teacher.objects.delete(id=0)
            return HttpResponse(status=204, headers={'HX-Trigger':'teacherChange', 'Department':department})
    else:
        if(id!=0):
            teacher=get_object_or_404(Teacher, pk=id)
            form=TeacherForm(instance=teacher)
        else:     
            form = TeacherForm(initial={"id":0})
    return render(request, 'forms/teacherForm.html', {"form":form})

def setAvailability(request, teacherid):
    context={}
    context['teacher']=Teacher.objects.get(id=teacherid)
    ft=context['teacher'].department.format
    periods=Period.objects.values_list().filter(department=context['teacher'].department)
    period1=periods[1]
    extra=ft.numPeriods*5
    formsets=[]

    availabilityFormSet = formset_factory(AvailabilityForm, extra=extra)
    if request.method=='POST':
        for w in range(ft.numWeeks):
            formset1 = availabilityFormSet(request.POST, prefix="week-"+str(w))
            if formset1.is_valid():
                i=0
                Availability.objects.filter(teacher=teacherid).filter(week=w+1).delete()
                for f in formset1:
                    cd = f.cleaned_data
                    checked = cd.get('checked')
                    if(checked):
                        newperiod=Availability()
                        newperiod.period=cd.get('period')
                        newperiod.week=cd.get('week')
                        newperiod.teacher=Teacher.objects.get(id=teacherid)
                        newperiod.save()
                    i=i+1
                valid=True
            else:
                valid=False
            formsets.append(formset1)
        if valid==True:
            return redirect(reverse('departments'))
    else:
        for w in range(ft.numWeeks):
            formsets.append(availabilityFormSet(prefix="week-"+str(w)))
        #formset2 = availabilityFormSet(prefix="week2")
    
    currentQuery=Availability.objects.filter(teacher=teacherid)
    current = []
    for c in currentQuery:
        current.append(str(c.week)+"-"+c.period)

    #hours=Teacher.objects.values_list('totalHours', flat=True).get(id=teacherid)
    #context['hours']=hours
    context['current']=current
    context['periods']=periods
    #context['formset1']=formset1
    context['formsets']=formsets
    context['weeks']=ft.numWeeks
    context['periodpw']=ft.numPeriods*5
    #context['formset2']=formset2
    return render(request, 'forms/availabilityForm.html', context)
