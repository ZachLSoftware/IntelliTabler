from django.shortcuts import get_object_or_404, render, redirect
from ..models import Department, Teacher, Module, ModuleGroup, Timetable, Period
from django.contrib.auth.decorators import login_required
from django.apps import apps



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
    modules=ModuleGroup.objects.filter(department=departmentId)
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
    modules=Module.objects.filter(teacher=teacher)
    context={}
    context['modules']=modules
    context["teacher"]=teacher
    return render(request, "data/teacherInfo.html", context)

def getModules(request, groupId=0):
    if groupId==0:
        groupId=request.GET.get('groupId', 0)        
    moduleList=Module.objects.filter(group_id=groupId)
    context={}
    modules={}
    for mod in moduleList:
        if mod.groupNum not in modules:
            modules[mod.groupNum]=[]
        modules[mod.groupNum].append(mod)
    context["modules"]=modules
    context["group"]=moduleList[0].group
    return render(request, "data/modulesInfo.html", context)

def timetableView(request, timetable):
    table=Timetable.objects.get(id=timetable)
    teachers=Teacher.objects.filter(department=table.year.department)
    periods=Period.objects.filter(department=table.year.department)
    context={'timetable':table, 'teachers':teachers, 'periods':periods}
    return render(request, 'data/timetable.html', context)