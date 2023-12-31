from django.urls import reverse
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from ..forms import *
from ..models import *
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, render, redirect
from django.apps import apps
import json
from ..helper_functions.serializers import *
from ..helper_functions.scripts import *
from django.contrib import messages
from ..helper_functions.toExcel import readFromCombing, templateBuilderMain, readInExcel


"""
Form handling for adding a new Department
"""
def addDepartment(request):

    if request.method == "POST":
        form = DepartmentForm(request.POST)

        #If valid, save new department from form data, return httpresponse to trigger evenet
        if form.is_valid():
            dep=Department()
            dep.name=form.cleaned_data['name']
            format = Format()
            format.numPeriods=form.cleaned_data['numPeriods']
            format.numWeeks=form.cleaned_data['numWeeks']
            format.department=dep
            dep.user=request.user
            dep.save()
            format.save()
            table=Timetable.objects.filter(tableYear__department=dep).first()

            #Create event and return
            event={'departmentAdded': {'tableId': table.id, 'departmentTitle':dep.name +" "+ str(table.tableYear.year)}}
            return HttpResponse(status=204, headers={'HX-Trigger':json.dumps(event)})
    
    else:
        form=DepartmentForm()
        
    context={
        "form": form,
        "Operation": "Add Department"
    }
    return render(request, 'forms/modalForm.html',context)


"""
Special view to handle change in department information.
"""
def editDepartment(request, departmentId):
    dep=get_object_or_404(Department, id=departmentId)
    if request.method== "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dep.name=form.cleaned_data['name']
            if dep.format.numWeeks!=form.cleaned_data['numWeeks']:
                dep.format.numWeeks=form.cleaned_data['numWeeks']
            if dep.format.numPeriods!=form.cleaned_data['numPeriods']:
                dep.format.numPeriods=form.cleaned_data['numPeriods']
            dep.save()
            dep.format.save()
            event={'departmentChanged': {'departmentName':dep.name, 'depId': dep.id}}
            return HttpResponse(status=204, headers={'HX-Trigger':json.dumps(event)})
    else:
        form=DepartmentForm(initial={'name':dep.name, 'numWeeks': dep.format.numWeeks, 'numPeriods':dep.format.numPeriods})
    context={
    "form": form,
    "Operation": "Edit Department"
    }
    return render(request, 'forms/modalForm.html',context)


"""
Add or edit teacher function
"""
def addTeacher(request, department, id=0):
    if request.method=="POST":

        #Get or create the teacher object for the form
        try:
            teacher=Teacher.objects.get(id=id)
            created=False
        except:
            teacher=Teacher.objects.create(department_id=department)
            created=True
        form = TeacherForm(request.POST, instance=teacher)
        if(form.is_valid()):
            newTeacher=form.cleaned_data
            newTeacher["department"]=Department.objects.get(id=department)
            teacher.save()

            #Return different event based on creation or editing
            if(not created):
                return HttpResponse(status=204, headers={'HX-Trigger':json.dumps({'teacherDetailsChange':'None', 'teacherChange':'None'}), 'Department':department})
            return HttpResponse(status=204, headers={'HX-Trigger':'teacherChange', 'Department':department})
        else:
            if created:
                teacher.delete()            
    else:
        if(id!=0):
            teacher=get_object_or_404(Teacher, pk=id)
            form=TeacherForm(instance=teacher)
        else:     
            form = TeacherForm()

    context={'form':form}
    context['Operation']="Add or Edit Teacher"
    return render(request, 'forms/modalForm.html', context)

"""
Availability Form handler
"""
def setAvailability(request, teacherid):
    context={}
    context['teacher']=get_object_or_404(Teacher, id=teacherid)
    ft=context['teacher'].department.format
    periods=Period.objects.values_list().filter(department=context['teacher'].department)
    extra=ft.numPeriods*5

    formsets=[]

    #Create Forms
    availabilityFormSet = formset_factory(AvailabilityForm, extra=extra)
    if request.method=='POST':

        #Iterate through each weeks formset
        for w in range(ft.numWeeks):
            formset1 = availabilityFormSet(request.POST, prefix="week-"+str(w))
            if formset1.is_valid():
                i=0
                Availability.objects.filter(teacher=teacherid).filter(period__week=w+1).delete()
                for f in formset1:
                    cd = f.cleaned_data
                    checked = cd.get('checked')
                    if(checked):
                        newperiod=Availability()
                        newperiod.period=Period.objects.get(department = context['teacher'].department, name=cd.get('period'), week=cd.get('week'))
                        newperiod.teacher=Teacher.objects.get(id=teacherid)
                        newperiod.save()
                    i=i+1
                valid=True
            else:
                valid=False
            formsets.append(formset1)
        if valid==True:
            return HttpResponse(status=204, headers= {"HX-Trigger": json.dumps({'successWithMessage': context['teacher'].name+" Availability Updated", 'availabilitySaved':'None'})})
    else:
        for w in range(ft.numWeeks):
            formsets.append(availabilityFormSet(prefix="week-"+str(w)))
    
    currentQuery=Availability.objects.filter(teacher=teacherid)
    current = []
    for c in currentQuery:
        current.append(str(c.period.week)+"-"+c.period.name)

    #Render Form context
    context['current']=current
    context['periods']=periods
    context['formsets']=formsets
    context['weeks']=ft.numWeeks
    context['offset']=ft.numPeriods
    return render(request, 'forms/availabilityForm.html', context)

"""
Add or edit Modules form handler
"""
def addModule(request, yearId, parentId=0):
    context={}
    department=Year.objects.get(id=yearId).department
    if request.method=='POST':

        #Try to get object for form, or build a new object
        if parentId!=0:
            parent=get_object_or_404(ModuleParent,pk=parentId)
            form=ModuleParentForm(request.POST, request.FILES, year=yearId, department=department, edit=True, instance=parent)
        else:
            form=ModuleParentForm(request.POST, request.FILES,year=yearId, department=department)

        #Check if valid and save
        if form.is_valid():
            if parentId==0:
                timetables=Timetable.objects.filter(tableYear_id=yearId)
                p=form.save(commit=False)
                for table in timetables:
                    p.pk=None
                    p.timetable=table
                    p.department=department
                    p.save()

                #Trigger event
                return HttpResponse(status=204, headers={'HX-Trigger':'moduleParentChange'})
            
            #If editing existing parent, edit all parents in the same year.
            else:
                parents=ModuleParent.objects.filter(sharedId=parent.sharedId)
                for p in parents:
                    p.name=form.cleaned_data['name']
                    p.numClasses=form.cleaned_data['numClasses']
                    p.numPeriods=form.cleaned_data['numPeriods']
                    p.repeat=form.cleaned_data['repeat']
                    p.color=form.cleaned_data['color']
                    p.save()
                return HttpResponse(status=204, headers={'HX-Trigger':'{"moduleDetailsChange":"None", "moduleParentChange": "None"}'})
            
    #If request is GET
    else:
        if(parentId!=0):
            parent=get_object_or_404(ModuleParent,pk=parentId)
            form=ModuleParentForm(year=yearId, department=department, edit=True, instance=parent)
            context['Operation']="Edit Classes"
        else:
            form=ModuleParentForm(year=yearId, department=department)
            context['Operation']="Add Classes"
    context['form']=form
    return render (request, "forms/modalForm.html", context)


"""
Add a new year to department.
"""
def addYear(request, departmentId=0):
    if(departmentId):
        dq=Department.objects.filter(id=departmentId)
    else:
        dq=Department.objects.filter(user=request.user)
    departments=[(d.id,d.name) for d in dq]
    
    if request.method=='POST':
        form=YearForm(departments, request.POST, request.FILES,)
        if form.is_valid():
            year=form.save(commit=False)
            year.department_id=form.cleaned_data['department']
            year.save()
            event={'yearAdded': {'tableId': year.defaultTimetable.id, 'departmentTitle':year.department.name +" "+ str(year.year)}}
            return HttpResponse(status=204, headers={'HX-Trigger': json.dumps(event)})
    else:
        form=YearForm(departments)
    context={}
    context['form']=form
    #context['departmentId']=departmentId
    context['Operation']="Add Year"
    return render(request, "forms/modalForm.html", context)


"""
Assign a teacher to a class
"""
def assignTeacher(request, departmentId, moduleId):
    #Get teachers for choice
    teachers=Teacher.objects.filter(department_id=departmentId).order_by('name')
    choices=[(teacher.id, teacher.name) for teacher in teachers]
    if request.method=='POST':
        form=AssignTeacherForm(choices, request.POST, request.FILES)
        if form.is_valid():
            module= Module.objects.get(id=moduleId)

            #Check if teacher is assigned to all of the same class
            if form.cleaned_data['assignToAll']:
                Module.objects.filter(sharedKey=module.sharedKey).update(teacher_id=int(form.cleaned_data['teacher']))

            #Save one class
            else:
                module.teacher_id=int(form.cleaned_data['teacher'])
                module.save()
            return HttpResponse(status=204, headers={'HX-Trigger':'moduleDetailsChange'})
    form=AssignTeacherForm(choices)
    context={'form':form}
    context['Operation']="Assign Teacher"
    return render(request, 'forms/modalForm.html', context)


"""
Handles assignment of classes in the combing chart
"""
def assignTeacherCombing(request, teacherId, timetableId):
    mods=Module.objects.filter(group__parent__timetable_id=timetableId, teacher__isnull=True).order_by('name')
    groups = list(set(mods.values_list('group__id', 'group__name').distinct()))
    parentChoices = list(set(mods.values_list('group__parent__id', 'group__parent__name').distinct()))
    modules=[(mod.id, mod.name) for mod in mods]
    newMods=[]

    if request.method=='POST':
        teachers=set()
        parents=set()
        teachers.add(teacherId)
        form=addTeacherCombingForm(parentChoices, groups, modules,request.POST,request.FILES)
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
                module_ser=ModuleSerializer(cl)
                module=module_ser.data
                module["session"]="#" + str(cl.teacher.id) +"x" + cl.group.period.name + "-"+ str(cl.group.period.week)
                module["teacher"]=cl.teacher.id
                module.pop('teacher', None)
                newMods.append(module)
            event={'modUpdate': {'newMods': newMods, 'teachers':list(teachers), 'parents':list(parents)}}
            return HttpResponse(status=204, headers={'HX-Trigger':json.dumps(event)})
            
        else:
            return render(request, 'forms/modalForm.html', {'form':form})

    else:
        form=addTeacherCombingForm(parentChoices,groups,modules)

    context={}
    context['form']=form
    return render(request, 'forms/modalForm.html', context)


def assignPeriod(request, department, groupId):
    weeks=[]
    periods=[]
    group=ModuleGroup.objects.get(id=groupId)
    format = Format.objects.get(department_id=department)
    for i in range(1, format.numPeriods+1):
        periods.append((i,i))
    for i in range(1, format.numWeeks+1):
        weeks.append((i,i))
    if request.method=='POST':
        form=AssignPeriodForm(weeks,periods,request.POST,request.FILES)
        if form.is_valid():
            per=form.cleaned_data['day']+"-"+str(form.cleaned_data['period'])
            modules=updatePeriod(group,per,form.cleaned_data['week'])
            event={"periodUpdate":{"modules":modules}}
            event["moduleDetailsChange"]="Modules Changed"
            return HttpResponse(status=204, headers={'HX-Trigger':json.dumps(event)})
    if group.period is not None:
        day,p=group.period.name.split('-')[0], group.period.name.split('-')[1]
        form=AssignPeriodForm(weeks,periods, initial={'week':group.period.week, 'day':day, 'period':p})
    else:
        form=AssignPeriodForm(weeks,periods)
    context={'form':form}
    context['Operation']="Assign/Edit Period"
    return render(request, 'forms/modalForm.html', context)


"""
Handle when a class is dropped on the calendar
"""
def calendarPeriodDrop(request, day, week, groupId):
    group=ModuleGroup.objects.get(id=groupId)
    modules=updatePeriod(group,day,week)
    current=next(i for i, g in enumerate(modules) if g['id']==groupId)
    del modules[current]
    event={"periodUpdate":{"modules":modules}}
    return HttpResponse(status=204,  headers={'HX-Trigger':json.dumps(event)})

"""
Handles deletion of objects
"""
def deleteObject(request, type, id):
    Type = apps.get_model(app_label='timetable', model_name=type)
    if type=="Timetable":
        t=Timetable.objects.get(id=id)
        year=t.tableYear
        if t==year.defaultTimetable:
            tables=Timetable.objects.filter(tableYear=year).exclude(id=id)
            if len(tables)>=1:
                year.defaultTimetable=tables.first()
                year.save()
            else:
                error = {"error": "Cannot delete the default timetable if it is the only table."}
                return JsonResponse(error, status="400")
        objId=str(year.defaultTimetable.id)
    else:
        objId=id
    if(Type==ModuleParent):
        objs=Type.objects.filter(sharedId=id)
        for obj in objs:
            obj.delete()
    else:
        try:
            obj = Type.objects.get(id=id).delete()
        except Type.DoesNotExist:
            obj=None
    
    #Create event based on type deleted
    trigger = type[0].lower()+type[1:]
    events={trigger+'Change': "Deleted", trigger+'Deleted':objId}
    return HttpResponse(status=204, headers={"HX-Trigger": json.dumps(events)})


"""
Handles adding a module via the calendar
"""
def addModuleCalendar(request, day, week, timetableId, teacher=0):
    groups=ModuleGroup.objects.filter(parent__timetable_id=timetableId, period__isnull=True).order_by('name')
    choices=[]
    for group in groups:
        choices.append((group.id, group.name))
        
    if request.method=='POST':
        form=addEventForm(choices, request.POST,request.FILES)
        if form.is_valid():
            mod=ModuleGroup.objects.get(id=form.cleaned_data["group"])
            events={}
            modules=updatePeriod(mod,day,week)
            events["addCalendarEvent"]={"modules":modules}
            return HttpResponse(status=204, headers={"HX-Trigger": json.dumps(events)})
    form=addEventForm(choices)
    context={'form':form}
    context['Operation']="Assign Class to Period"
    return render(request, 'forms/modalForm.html', context)


"""
Handels unassigning a teacher
"""
def unassignTeacher(request, modId):
    if request.method=='POST':
        mod=Module.objects.get(id=modId)
        event={"unassignSuccess": {"modId":modId, "parent":[mod.group.parent.id], "teacher":[mod.teacher.id]}}
        mod.teacher=None
        mod.save()
        return HttpResponse(status=204, headers={"HX-Trigger": json.dumps(event)})

"""
Handles dropping of module in combing chart
"""
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
        module_ser=ModuleSerializer(cl)
        module=module_ser.data
        module["session"]="#" + str(cl.teacher.id) +"x" + cl.group.period.name + "-"+ str(cl.group.period.week)
        module["teacher"]=cl.teacher.id
        module.pop('teacher', None)
        newMods.append(module)
    event={'modUpdate': {'newMods': newMods, 'teachers':list(teachers), 'parents':list(parents)}}
    return HttpResponse(status=204, headers={'HX-Trigger':json.dumps(event)})

"""
Simple color change form
"""
def changeColor(request, parentId):
    p=ModuleParent.objects.get(id=parentId)
    if request.method=='POST':
        form=changeColorForm(request.POST, request.FILES)
        if form.is_valid():
            p=ModuleParent.objects.get(id=parentId)
            p.color=form.cleaned_data['color']
            p.save()
            events={'moduleDetailsChange':p.color, 'updateColor': {'parentId': p.id, 'color':p.color}}
            return HttpResponse(status=204, headers={'HX-Trigger':json.dumps(events)})
    form=changeColorForm(initial={'color':p.color})
    return render(request, "forms/modalForm.html", {'Operation':'Change Color', 'form':form})

"""
Handles changing from light to dark themes
"""
def changeTheme(request, theme, timetableId=0):
    if theme != request.user.theme:
        request.user.theme=theme
        request.user.save()
        response = redirect('dashboard')
        request.session['timetableId']=timetableId
        return response
    else:
        return HttpResponse(status=204)

"""
Adds a new timetable.
"""
def addTimetable(request, yearId, timetableId=0):
    #Try to get a timetable object, else create a new one.
    try:
        table=Timetable.objects.get(id=timetableId)
    except:
        table=Timetable()
    
    #Post form processing
    if request.method=="POST":
        form = TimetableForm(request.POST, request.FILES, instance=table)
        if form.is_valid():
            table=form.save(commit=False)
            table.tableYear_id=yearId
            table.save()

            #If set to be default, get year object and update
            if form.cleaned_data['default']:
                Year.objects.filter(id=yearId).update(defaultTimetable=table)
            
            #Return timetable id in httpresponse
            events={'timetableAdded': str(table.id)}
            return HttpResponse(204, headers={"HX-Trigger":json.dumps(events)})
    #GET request form
    else:
        form = TimetableForm(instance=table)
    return render(request, "forms/modalForm.html", {'Operation':'Add Timetable', 'form':form})

def setDefaultTimetable(request, yearId, timetableId):
    Year.objects.filter(id=yearId).update(defaultTimetable_id=timetableId)
    return HttpResponse(204, headers= {"HX-Trigger": json.dumps({'successWithMessage': 'Default timetable updated'})})

    
def timetableWizard(request, timetableA):
    timetable=Timetable.objects.get(id=timetableA)
    tables=Timetable.objects.filter(tableYear=timetable.tableYear).order_by('name')
    context={'timetable':timetable, 'department': timetable.tableYear.department, 'tables':tables, 'timetableId':0}
    response=render(request,'forms/timetableWizard.html', context)

    #Creates an event trigger when content is loaded
    response['HX-Trigger']='dashboardLoaded'
    return response

def addPreference(request, timetableId, teacherId):        
    moduleparents=ModuleParent.objects.filter(timetable_id=timetableId).order_by('name')
    parents=[(mp.id, mp.name) for mp in moduleparents]
    grs=ModuleGroup.objects.filter(parent__timetable_id=timetableId).order_by('name')
    mods=Module.objects.filter(group__parent__timetable_id=timetableId).order_by('name')
    groups=[(group.id, group.name) for group in grs]
    modules=[(mod.id, mod.name) for mod in mods]
    if request.method=='POST':
        form=setPreferenceForm(parents, groups, modules, request.POST, request.FILES, teacherId=teacherId)
        if form.is_valid():
            mod = Module.objects.get(id=form.cleaned_data['module'])
            if form.cleaned_data['assignToAll']:
                modules=Module.objects.filter(sharedKey=mod.sharedKey)
            else: modules=[mod]
            for m in modules:
                p=Preference()
                p.teacher_id=teacherId
                p.module=m
                p.timetable_id=timetableId
                p.priority=form.cleaned_data['priority']
                p.save()
            events={'preferenceChange': "None"}
            return HttpResponse(status=204, headers={'HX-Trigger':json.dumps(events)})
    else:
        form=setPreferenceForm(parents)
    return render(request, "forms/modalForm.html", {'Operation':'Set Preference', 'form':form})


def getTemplateFileTest(request, timetableId):
    timetable=Timetable.objects.get(id=timetableId)
    if request.method=="POST":
        form=UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                results = readInExcel(timetable,request.FILES['file'])
            except Exception as msg:
                form.add_error('file','There was a problem with reading your file.')
                return render(request, 'forms/modalForm.html', {'form':form})
            if not all(val == False for val in results.values()):
                if all( val == True for val in results.values()):
                    return HttpResponse(204, headers= {"HX-Trigger": json.dumps({'successWithMessage': 'Timetable has been updated'})})
                else:
                    message='Not all worksheets were able to update.\n'
                    for k,v in results.items():
                        if v == False:
                            message=message + 'Worksheet ' + k + ' had invalid data.\n'
                    return HttpResponse(204, headers= {"HX-Trigger": json.dumps({'warningWithMessage': message})})
            else:
                form.add_error('file','There were invalid or missing required values in the upload.')
    else:
        form=UploadFileForm()
    return render(request, 'forms/modalForm.html', {'form':form})

def templateBuilderInstructions(request, timetableId):
    return render(request, 'data/templateInstructions.html', {'timetableId':timetableId})


def templateBuilder(request, timetableId):
    if request.method=='POST':

        choices=[]
        form=TemplateChoices(request.POST)
        if form.is_valid():
            for k,v in form.cleaned_data.items():
                if v:
                    choices.append(k)
        download_url = reverse('templateBuilderDownload', args=[timetableId, json.dumps(choices)])
        return render(request, 'data/downloadFile.html', {'file_url': download_url})
    else:
        form=TemplateChoices()
    return render(request, "forms/modalForm.html", {'form':form, 'Operation':'Template Builder'})

def templateBuilderDownload(request, timetableId, choices):
        timetable=Timetable.objects.get(id=timetableId)
        choices=json.loads(choices)
        template=templateBuilderMain(timetable, choices)
        response = HttpResponse(template,content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=TimetableDataTemplate.xlsx'
        return response