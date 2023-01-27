from django.shortcuts import get_object_or_404, render, redirect
from ..models import Department, Teacher, Module, ModuleGroup, Timetable, Period, ModuleParent, Format, Year
from django.contrib.auth.decorators import login_required
from django.apps import apps
import json
from django.http import JsonResponse



def index(request):
    return render(request, "index.html")

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

@login_required
def viewModules(request, type, departmentId, yearId=0):
    context={}
    Type = apps.get_model(app_label='timetable', model_name=type)
    if yearId==0:
        yearId=request.GET.get('yearId', 0)
    if(yearId):
        objects=Type.objects.filter(user=request.user, year=yearId)
    else:
        objects=Type.objects.filter(department_id=departmentId)
    context['type']= type
    context["entities"]=objects
    context["departmentId"]=departmentId
    context["yearId"]=yearId
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
        years.add(mod.year)
        if(mod.year not in context):
            context[mod.year]=[]
        context[mod.year].append(mod)
    context["years"]=years
    context["departmentId"]=departmentId
    context["departments"]=departments
    return render(request, "data/modules.html", context)



def getTeacher(request, id=0):
    if id==0:
        id=request.GET.get('id', 0)
    try: 
        teacher=Teacher.objects.get(id=id)
    except:
        teacher=None
    mods=Module.objects.filter(teacher=teacher)
    modules={}
    for mod in mods:
        if mod.group.parent.year.year not in modules:
            modules[mod.group.parent.year.year]=[]
        modules[mod.group.parent.year.year].append(mod)
    context={}
    context['modules']=modules
    context["teacher"]=teacher
    return render(request, "data/teacherInfo.html", context)

def getModules(request, groupId=0):
    calendar=request.GET.get('calendar',0)
    if groupId==0:
        groupId=request.GET.get('groupId', 0) 
    if calendar:
        moduleList=Module.objects.filter(group_id=groupId) 
    else:      
        moduleList=Module.objects.filter(group__parent_id=groupId)
    context={}
    modules={}
    for mod in moduleList:
        if mod.group not in modules:
            modules[mod.group]=[]
        modules[mod.group].append(mod)
    context["modules"]=modules
    context["group"]=moduleList[0].group.parent
    return render(request, "data/modulesInfo.html", context)

def combingView(request, yearId):
    context={}
    year=Year.objects.get(id=yearId)
    teachers=Teacher.objects.filter(department=year.department)
    periods=Period.objects.filter(department=year.department)
    classes=Module.objects.filter(group__parent__year=year).order_by('group_id', 'name')
    unassigned = False
    modules=[]
    count={}
    parents=set()
    
    for cl in classes:
        if cl.group.period:
            parents.add(cl.group.parent)
            if cl.teacher:
                if cl.teacher in count:
                    count[cl.teacher]+=1
                else:
                    count[cl.teacher]=1
                info = {}
                info["id"]=cl.id
                info["module"]= {
                    "period": cl.group.period.name,
                    "week": cl.group.period.week,
                    "session": count[cl.teacher],
                    "name": cl.name,
                    "teacher": cl.teacher.id,
                    "groupid": cl.group.id,
                    "parent": cl.group.parent.id,
                    "color": cl.group.parent.color
                }
                modules.append(info)
        else:
            unassigned=True
            break
    

    
    context['modules']=json.dumps(modules)
    context['teachers']=teachers
    context['periods']=periods
    context['numPeriods']=len(periods)
    context['unassigned']=unassigned
    context['parents']=parents
    return render(request, 'data/combingView.html', context)

def calendarView(request, year, teacher=0):
    y=Year.objects.get(id=year)
    if teacher:
        title=Teacher.objects.get(id=teacher).name + " - "   + y.department.name + " - "+ str(y.year)
    else:
       title = y.department.name + " - " + str(y.year)
    context={'year':year, 'teacher':teacher, 'title':title}
    return render(request, 'data/calendarView.html', context)

def getCalendar(request, year, teacher=0):
    events={}
    modules=[]
    context={}
    if teacher:
        classes=Module.objects.filter(teacher_id=teacher, group__parent__year_id=year)
        for cl in classes:
            if cl.group.period:
                info = {}
                info["id"]=cl.id
                info["module"]= {
                    "period": cl.group.period.name,
                    "week": cl.group.period.week,
                    "name": cl.name,
                    "groupid": cl.group.id,
                    "parent": cl.group.parent.id,
                    "color": cl.group.parent.color
                }
                
                modules.append(info)
    else:
        classes=ModuleGroup.objects.filter(parent__year_id=year)
        for cl in classes:
            if cl.period:
                info = {}
                info["id"]=cl.id
                info["module"]= {
                    "period": cl.period.name,
                    "week": cl.period.week,
                    "name": cl.name,
                    "groupid": cl.id,
                    "parent": cl.parent.id,
                    "color": cl.parent.color
                }
                
                modules.append(info)

    events["modules"]=modules
    format=Format.objects.get(department=Year.objects.get(id=year).department)
    context['periods']=format.numPeriods
    context['weeks']=format.numWeeks

    context['events']=json.dumps(events)
    context['year']=year
    context['teacher']=teacher
    return render(request, 'data/calendarSetVariables.html', context)

def getCalendarData(year):
    classes=ModuleGroup.objects.filter(parent__year_id=year)
    events={}
    modules=[]
    for cl in classes:
        if cl.period:
            info = {}
            info["id"]=cl.id
            info["module"]= {
                "period": cl.period.name,
                "week": cl.period.week,
                "name": cl.name,
                "parent": cl.parent.id,
                "color": cl.parent.color
            }
            
            modules.append(info)
    events["modules"]=modules
    context={}
    context['events']=events
    return JsonResponse(events)