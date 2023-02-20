from django.shortcuts import get_object_or_404, render, redirect
from ..models import Department, Teacher, Module, ModuleGroup, Timetable, Period, ModuleParent, Format, Year
from django.contrib.auth.decorators import login_required
from django.apps import apps
import json
from django.http import JsonResponse
from ..serializers import *
from rest_framework.renderers import JSONRenderer




def index(request):
    return redirect('dashboard')

@login_required
def dashboard(request):
    context={}
    ds=Department.objects.filter(user=request.user)
    departments={}
    for d in ds:
        departments[d]=Year.objects.filter(department_id=d.id)
    context['departments']=departments
    context['template']="dashboard_"+request.user.theme+".html"
    return render(request, "dashboard.html", context)

def displayDashboardContent(request, timetableId):
    timetable=Timetable.objects.get(id=timetableId)
    tables=Timetable.objects.filter(tableYear=timetable.tableYear)
    context={'timetable':timetable, 'department': timetable.tableYear.department, 'tables':tables}
    response=render(request,'data/dashboardNav.html', context)
    response['HX-Trigger']='dashboardLoaded'
    return response

@login_required
def departments(request):
    return render(request, "data/departments.html")

@login_required
def departmentChange(request):
    context={}
    departments=Department.objects.filter(user=request.user)
    context["entities"]=departments
    return render(request, "data/sideBarList.html", context)

@login_required
def teachers(request):
    return render(request, "data/teachers.html")

@login_required
def teacherChange(request):
    context={}
    teachers=Teacher.objects.filter(user=request.user)
    context["entities"]=teachers
    return render(request, "data/sideBarList.html", context)

@login_required
def viewObjects(request, type, id=0):
    context={}
    Type = apps.get_model(app_label='timetable', model_name=type)
    if id==0:
        id=request.GET.get('id', 0)
    if(id):
        objects=Type.objects.filter(user=request.user, department_id=id)
    else:
        objects=Type.objects.filter(user=request.user)
    context['type']= type
    context["entities"]=objects
    context["objectId"]=id
    return render(request, "data/sideBarList.html", context)

def getList(request, type, timetableId):
    timetable=Timetable.objects.get(id=timetableId)
    context={'timetable':timetable}
    if type.upper()=='MODULEPARENT':
        objects=ModuleParent.objects.filter(timetable=timetable).order_by('name')
        context['type']='module'
        context['detailPath']='getModules'
        context['addPath']='addModule'
        context['addId']=timetable.tableYear.id
    elif type.upper()=='TEACHER':
        objects=Teacher.objects.filter(department=timetable.tableYear.department).order_by('name')
        context['type']=type
        context['detailPath']='getTeacher'
        context['addPath']='addTeacher'
        context['addId'] = timetable.tableYear.department.id
    context["objects"]=objects
    return render(request, "data/buttonSidebar.html", context)

def getSidebar(request, type, timetableId):
    timetable=Timetable.objects.get(id=timetableId)
    context={
        'type':type, 
        'infoType': type,
        'timetable': timetable,
        'detailPath': 'getTeacher',
    }
    if type.upper()=='MODULEPARENT':
        context['infoType']='module'
        context['detailPath']='getModules'
    return render(request, 'data/sidebarTemplate.html', context)

@login_required
def viewModules(request, type, departmentId, timetableId=0):
    context={}
    Type = apps.get_model(app_label='timetable', model_name=type)
    if(timetableId):
        objects=Type.objects.filter(user=request.user, timetable=timetableId)
    else:
        objects=Type.objects.filter(department_id=departmentId)
    context['type']= type
    context["entities"]=objects
    context["departmentId"]=departmentId
    context["timetableId"]=timetableId
    return render(request, "data/modulesList.html", context)

def modules(request, departmentId=0):
    context={}
    departments=Department.objects.filter(user=request.user)
    if(not departmentId):
        context["departments"]=departments
        context["departmentId"]=0
        return render(request, "data/modules.html", context)
    modules=ModuleParent.objects.filter(department=departmentId)
    years=set()
    for mod in modules:
        years.add(mod.timetable.tableYear)
        if(mod.year not in context):
            context[mod.year]=[]
        context[mod.year].append(mod)
    context["years"]=years
    context["departmentId"]=departmentId
    context["departments"]=departments
    return render(request, "data/modules.html", context)



def getTeacher(request, id=0, timetableId=0):
    if id==0:
        id=request.GET.get('id', 0)
    try: 
        teacher=Teacher.objects.get(id=id)
    except:
        teacher=None
    mods=Module.objects.filter(teacher=teacher, group__parent__timetable_id=timetableId)
    context={}
    context['modules']=mods
    context["teacher"]=teacher
    context["timetable"]=timetableId
    return render(request, "data/teacherInfo.html", context)

def getModules(request, groupId=0, timetableId=0):
    calendar=request.GET.get('calendar',0)
    if groupId==0:
        groupId=request.GET.get('groupId', 0) 
    if calendar:
        moduleList=Module.objects.filter(group_id=groupId).order_by('name')
    else:      
        moduleList=Module.objects.filter(group__parent_id=groupId).order_by('group__name','name')
    context={}
    modules={}
    for mod in moduleList:
        if mod.group not in modules:
            modules[mod.group]=[]
        modules[mod.group].append(mod)
    context["modules"]=modules
    context["parent"]=moduleList[0].group.parent
    context["group"]=groupId
    return render(request, "data/modulesInfo.html", context)

def combingView(request, timetableId):
    context={}
    timetable=Timetable.objects.get(id=timetableId)
    teachers=Teacher.objects.filter(department=timetable.tableYear.department)
    periods=list(Period.objects.filter(department=timetable.tableYear.department))
    groups=ModuleGroup.objects.filter(parent__timetable=timetable).order_by('parent__name', 'id')
    classes=Module.objects.filter(group__parent__timetable=timetable).order_by('group__parent__name','group_id', 'name')
    unassigned = False
    modules=[]
    parents=set()
    pAssign={}
    mJson={}
    index=1
    for group in groups:
        if group.period not in periods:
            continue
        else:
            pAssign[index]=group.period
            periods.remove(group.period)
            index+=1
    if periods:
        for period in periods:
            pAssign[index]=period
            index+=1
    
    for cl in classes:
        if cl.group.period:
            parents.add(cl.group.parent)
            if cl.group.id not in mJson:
                mJson[cl.group.id]=[]
            mJson[cl.group.id].append((cl.id,cl.name))
            if cl.teacher:
                module_ser=ModuleSerializer(cl)
                module=module_ser.data
                module["session"]="#" + str(cl.teacher.id) +"x" + cl.group.period.name + "-"+ str(cl.group.period.week)
                module["teacher"]=cl.teacher.id
                module.pop('teacher', None)
            
                modules.append(module)
        else:
            unassigned=True
            modules=[]
            break
    

    
    context['modules']=json.dumps(modules)
    context['teachers']=teachers
    context['periods']=pAssign
    context['numPeriods']=len(periods)
    context['unassigned']=unassigned
    context['parents']=parents
    context['timetableId']=timetableId
    context['modChoices']=json.dumps(mJson)
    return render(request, 'data/combingView.html', context)

def calendarView(request, timetableId, teacher=0):
    t=Timetable.objects.get(id=timetableId)
    if teacher:
        title=Teacher.objects.get(id=teacher).name + " - "   + t.tableYear.department.name + " - "+ str(t.name)
    else:
       title = t.tableYear.department.name + " - " + str(t.name)
    context=getCalendar(timetableId, teacher)
    context['title']=title
    return render(request, 'data/calendarView.html', context)

def getCalendar(timetableId, teacher=0):
    events={}
    modules=[]
    context={}
    if teacher:
        classes=Module.objects.filter(teacher_id=teacher, group__parent__timetable_id=timetableId)
        for cl in classes:
            if cl.group.period:
                module_ser=ModuleSerializer(cl)
                module=module_ser.data
                module['parent']=module['group']['parent']
                module['period']=module['group']['period']
                module['groupid']=module['group']['id']
                module.pop('group', None)
                module.pop('teacher', None)
                
                modules.append(module)
    else:
        classes=ModuleGroup.objects.filter(parent__timetable_id=timetableId)
        for cl in classes:
            if cl.period:
                module_ser=ModuleGroupSerializer(cl)
                module=module_ser.data
                module['groupid']=module_ser.data['id']
                modules.append(module)

    events["modules"]=modules
    format=Format.objects.get(department=Timetable.objects.get(id=timetableId).tableYear.department)
    context['periods']=format.numPeriods
    context['weeks']=format.numWeeks

    context['events']=json.dumps(events)
    context['timetable']=timetableId
    context['teacher']=teacher
    return context

def getCalendarData(timetableId):
    classes=ModuleGroup.objects.filter(parent__timetable_id=timetableId)
    events={}
    modules=[]
    for cl in classes:
        if cl.period:
            module_ser=ModuleGroupSerializer(cl)
            module=module_ser.data
            module['groupid']=module_ser.data['id']
            modules.append(module)
    events["modules"]=modules
    context={}
    context['events']=events
    return JsonResponse(events)