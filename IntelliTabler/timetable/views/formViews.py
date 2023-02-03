from django.urls import reverse
from django.http import HttpResponse
from ..forms import *
from ..models import *
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, render, redirect
from django.apps import apps
import json

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
            if(not created):
                return HttpResponse(status=204, headers={'HX-Trigger':'teacherDetailChange', 'Department':department})
            return HttpResponse(status=204, headers={'HX-Trigger':'teacherChange', 'Department':department})
            
    else:
        if(id!=0):
            teacher=get_object_or_404(Teacher, pk=id)
            form=TeacherForm(instance=teacher)
        else:     
            form = TeacherForm(initial={"id":0})
    context={'form':form}
    context['Operation']="Add or Edit Teacher"
    return render(request, 'forms/modalForm.html', context)

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
    context['offset']=ft.numPeriods
    #context['formset2']=formset2
    return render(request, 'forms/availabilityForm.html', context)


def addModule(request, year, groupId=0):
    context={}
    department=Year.objects.get(id=year).department
    if request.method=='POST':
        if groupId!=0:
            group=get_object_or_404(ModuleParent,pk=groupId)
            form=ModuleParentForm(request.POST, request.FILES,year=year, department=department, edit=True, instance=group)
        else:
            form=ModuleParentForm(request.POST, request.FILES,year=year, department=department)
        if form.is_valid():
            group=form.save(commit=False)
            group.year_id=year
            group.department=department
            group.user=request.user
            group.save()
            return HttpResponse(status=204, headers={'HX-Trigger':'moduleChange'})
    else:
        if(groupId!=0):
            group=get_object_or_404(ModuleParent,pk=groupId)
            form=ModuleParentForm(year=year, department=department, edit=True, instance=group)
            context['Operation']="Edit Modules"
        else:
            form=ModuleParentForm(year=year, department=department)
            context['Operation']="Add Modules"
    context['form']=form
    return render (request, "forms/modalForm.html", context)

def addYear(request, departmentId):
    
    if request.method=='POST':
        form=YearForm(request.POST, request.FILES)
        if form.is_valid():
            year=form.save(commit=False)
            year.department_id=departmentId
            year.save()
            return HttpResponse(status=204, headers={'HX-Trigger':'yearChange'})
    else:
        form=YearForm()
    context={}
    context['form']=form
    context['departmentId']=departmentId
    context['Operation']="Add Year"
    return render(request, "forms/modalForm.html", context)

def assignTeacher(request, departmentId, moduleId):
    choices=[]
    teachers=Teacher.objects.filter(department_id=departmentId)
    for teacher in teachers:
        choices.append((teacher.id, teacher.name))
    if request.method=='POST':
        form=AssignTeacherForm(choices, request.POST, request.FILES)
        if form.is_valid():
            module= Module.objects.get(id=moduleId)
            if form.cleaned_data['assignToAll']:
                modules=Module.objects.filter(group__parent=module.group.parent, name=module.name)
                for mod in modules:
                    mod.teacher_id=int(form.cleaned_data['teacher'])
                    mod.save()
            else:
                module.teacher_id=int(form.cleaned_data['teacher'])
                module.save()
            return HttpResponse(status=204, headers={'HX-Trigger':'moduleDetailsChange'})
    form=AssignTeacherForm(choices)
    context={'form':form}
    context['Operation']="Assign Teacher"
    return render(request, 'forms/modalForm.html', context)

def assignTeacherCombing(request, teacherId, yearId):
    g=ModuleGroup.objects.filter(parent__year_id=yearId)
    m=Module.objects.filter(group__parent__year_id=yearId)
    groups=[]
    moduleChoices=[]
    newMods=[]
    for group in g:
        groups.append((group.id, group.name))
    for module in m:
        moduleChoices.append((module.id, module.name))

    if request.method=='POST':
        teachers=set()
        parents=set()
        teachers.add(teacherId)
        form=addTeacherCombingForm(groups,moduleChoices,request.POST,request.FILES)
        if form.is_valid():
            groupId=form.cleaned_data['group']
            modId=form.cleaned_data['module']
            group=ModuleGroup.objects.get(id=groupId)
            module=Module.objects.get(id=modId)
            if form.cleaned_data['assignToAll']:
                modules=Module.objects.filter(group__parent=group.parent, name=module.name)
            else:
                modules=[module]
            for cl in modules:
                if cl.teacher_id:
                    teachers.add(cl.teacher_id)
                parents.add(cl.group.parent_id)
                cl.teacher_id=teacherId
                cl.save()
                info = {}
                info["id"]=cl.id
                info["module"]= {
                    "period": cl.group.period.name,
                    "week": cl.group.period.week,
                    "session": "#" + str(cl.teacher.id) +"x" + cl.group.period.name + "-"+ str(cl.group.period.week),
                    "name": cl.name,
                    "teacher": cl.teacher.id,
                    "groupid": cl.group.id,
                    "parent": cl.group.parent.id,
                    "color": cl.group.parent.color
                }
                newMods.append(info)
            event={'modUpdate': {'newMods': newMods, 'teachers':list(teachers), 'parents':list(parents)}}
            return HttpResponse(status=204, headers={'HX-Trigger':json.dumps(event)})
            
        else:
            return render(request, 'forms/modalForm.html', {'form':form})

    else:
        form=addTeacherCombingForm(groups,moduleChoices)

    context={}
    context['form']=form
    return render(request, 'forms/modalForm.html', context)


def assignPeriod(request, department, groupId):
    weeks=[]
    periods=[]
    format = Format.objects.get(department_id=department)
    for i in range(1, format.numPeriods+1):
        periods.append((i,i))
    for i in range(1, format.numWeeks+1):
        weeks.append((i,i))
    if request.method=='POST':
        form=AssignPeriodForm(weeks,periods,request.POST,request.FILES)
        if form.is_valid():
            group=ModuleGroup.objects.get(id=groupId)
            per=form.cleaned_data['day']+"-"+str(form.cleaned_data['period'])
            group.period=Period.objects.get(department_id=department, week=form.cleaned_data['week'], name=per)
            group.save()
            info = {}
            info["id"]=group.id
            info["module"]= {
                "period": group.period.name,
                "week": group.period.week,
                "name": group.name,
                "parent": group.parent.id,
                "color": group.parent.color
            }
            event={"periodUpdate":info}
            event["moduleDetailsChange"]="Modules Changed"
            return HttpResponse(status=204, headers={'HX-Trigger':json.dumps(event)})
    form=AssignPeriodForm(weeks,periods)
    context={'form':form}
    context['Operation']="Assign/Edit Period"
    return render(request, 'forms/modalForm.html', context)

def calendarPeriodDrop(request, day, week, groupId):
    group=ModuleGroup.objects.get(id=groupId)
    period=Period.objects.get(department=group.parent.department, name=day, week=week)
    group.period=period
    group.save()
    return HttpResponse(status=204)

def deleteObject(request, type, id):
    Type = apps.get_model(app_label='timetable', model_name=type)
    try:
        obj = Type.objects.get(id=id).delete()
    except Type.DoesNotExist:
        obj=None
    trigger = type[0].lower()+type[1:]+"Change"
    events='{\"'+trigger+'\": "Deleted", "objectDeleted": "ObjectDeleted"}'
    return HttpResponse(status=204, headers={"HX-Trigger": events})

def addModuleCalendar(request, day, week, year):
    groups=ModuleGroup.objects.filter(parent__year_id=year, period__isnull=True)
    choices=[]
    for group in groups:
        choices.append((group.id, group.name))
        
    if request.method=='POST':
        form=addEventForm(choices, request.POST,request.FILES)
        if form.is_valid():
            mod=ModuleGroup.objects.get(id=form.cleaned_data["group"])
            department=Year.objects.get(id=year).department
            period=Period.objects.get(department=department, name=day, week=week)
            mod.period=period
            mod.save()
            events={}
            modules=[]
            info = {}
            info["id"]=mod.id
            info["module"]= {
                "period": mod.period.name,
                "week": mod.period.week,
                "name": mod.name,
                "parent": mod.parent.id,
                "color": mod.parent.color
            }
            modules.append(info)
            events["addEvent"]={"modules":modules}
            #events='{"addEvent": {"cellId": \"'+day+'-'+str(week)+'\", "mod":"'+form.cleaned_data["group"]+'"} }'
            return HttpResponse(status=204, headers={"HX-Trigger": json.dumps(events)})
    form=addEventForm(choices)
    context={'form':form}
    context['Operation']="Assign Module Timeslot"
    return render(request, 'forms/modalForm.html', context)

def unassignTeacher(request, modId):
    if request.method=='POST':
        mod=Module.objects.get(id=modId)
        event={"unassignSuccess": {"modId":modId, "parent":[mod.group.parent.id], "teacher":[mod.teacher.id]}}
        mod.teacher=None
        mod.save()
        return HttpResponse(status=204, headers={"HX-Trigger": json.dumps(event)})

def assignTeacherDrop(request, teacherId, modId):
    if request.method=='POST':
        teachers=set()
        parents=set()
        teachers.add(teacherId)
        cl=Module.objects.get(id=modId)
        teachers.add(cl.teacher_id)
        cl.teacher_id=teacherId
        newMods=[]
        cl.save()
        parents.add(cl.group.parent_id)
        cl.teacher_id=teacherId
        cl.save()
        info = {}
        info["id"]=cl.id
        info["module"]= {
            "period": cl.group.period.name,
            "week": cl.group.period.week,
            "session": "#" + str(cl.teacher.id) +"x" + cl.group.period.name + "-"+ str(cl.group.period.week),
            "name": cl.name,
            "teacher": cl.teacher.id,
            "groupid": cl.group.id,
            "parent": cl.group.parent.id,
            "color": cl.group.parent.color
        }
        newMods.append(info)
    event={'modUpdate': {'newMods': newMods, 'teachers':list(teachers), 'parents':list(parents)}}
    return HttpResponse(status=204, headers={'HX-Trigger':json.dumps(event)})


