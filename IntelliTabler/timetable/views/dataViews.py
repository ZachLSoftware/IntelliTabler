from django.shortcuts import get_object_or_404, render, redirect
from ..models import Department, Teacher, Module, ModuleGroup, Timetable, Period, ModuleParent, Format, Year
from django.contrib.auth.decorators import login_required
from django.apps import apps
import json
from django.http import JsonResponse
from ..serializers import *
from rest_framework.renderers import JSONRenderer
from ..csp import *
from django.http import HttpResponse
from django.contrib import messages
from ..toExcel import *


###Default Landing Page###
def index(request):
    return redirect('dashboard')


"""dashboard gets all departments from the user and creates a dictionary
with years as their values.
"""
@login_required
def dashboard(request):
    context={}

    #Get Departments based on user and create dictionary for dropdowns
    ds=Department.objects.filter(user=request.user).order_by('name')
    context['departments']={d:Year.objects.filter(department_id=d.id).order_by('year') for d in ds}
    context['template']="dashboard_"+request.user.theme+".html"
    return render(request, "dashboard.html", context)

"""Sets the current timetable and gets all available timetables for the year.
Creates the side navbar with the correct links for the timetable.
"""
def displayDashboardContent(request, timetableId):

    #Get requested timetable and other timetables in the same year
    timetable=Timetable.objects.get(id=timetableId)
    tables=Timetable.objects.filter(tableYear=timetable.tableYear).order_by('name')
    context={'timetable':timetable, 'department': timetable.tableYear.department, 'tables':tables}
    response=render(request,'data/dashboardNav.html', context)

    #Creates an event trigger when content is loaded
    response['HX-Trigger']=json.dumps({"sidebarLoaded":timetableId})
    return response


"""Gets necessary elements to display on the timetable information page.
"""
def displayTimetableLanding(request, timetableId):
    #Get timetable information with teachers and classes
    timetable=Timetable.objects.get(id=timetableId)
    teachers=Teacher.objects.filter(department=timetable.tableYear.department).order_by('name')
    classes=ModuleParent.objects.filter(timetable=timetable)
    weeks=timetable.tableYear.department.format.numWeeks

    #Get available teacher load
    totalTeacherLoad=0
    for teacher in teachers:
        totalTeacherLoad+=teacher.load

    #Get total number of classes per week
    weekLoads={}
    for week in range(1,weeks+1):
        weekLoads[week]=len(Module.objects.filter(group__parent__timetable=timetable, group__period__week=week))

    #Get Assigned Class totals
    assigned=len(Module.objects.filter(group__parent__timetable=timetable, teacher__isnull=False))

    #Get total number of classes in timetable
    totalClassLoad=len(Module.objects.filter(group__parent__timetable=timetable))

    #Set context
    context={'timetable':timetable,
             'teachers':teachers, 
             'classes':classes,
             'totalTeacherLoad':totalTeacherLoad,
             'weekLoads':weekLoads,
             'totalClassLoad':totalClassLoad,
             'assigned':assigned,
             'weeks':weeks}
    return render(request, 'data/timetableLandingPage.html', context)

"""getList gets a type and the current timetableId.
Returns instances of the type in order to create a 
list of items for the dashboard sidebar.
"""
def getList(request, type, timetableId):
    #Get current Timetable
    timetable=Timetable.objects.get(id=timetableId)
    context={'timetable':timetable}

    #Get items of Type. Sets paths for setting hx-get functions
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

#Creates the necessary elements for the Teacher and Module page to list items
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


def getTeacher(request, id=0, timetableId=0):
    if id==0:
        id=request.GET.get('id', 0)
    try: 
        teacher=Teacher.objects.get(id=id)
    except:
        teacher=None
    mods=Module.objects.filter(teacher=teacher, group__parent__timetable_id=timetableId).order_by('name', 'group__period')
    parents=ModuleParent.objects.filter(timetable_id=timetableId).order_by('name')
    context={}
    modules={key: [mod for mod in mods if mod.group.parent==key] for key in parents if any(mod.group.parent == key for mod in mods)}
    context['modules']=modules
    context["teacher"]=teacher
    context["timetable"]=timetableId
    return render(request, "data/teacherInfo.html", context)

def getModules(request, groupId=0, timetableId=0):
    calendar=request.GET.get('calendar',0)
    if groupId==0:
        groupId=request.GET.get('groupId', 0) 
    if calendar:
        moduleList=Module.objects.filter(group_id=groupId).order_by('lesson')
    else:      
        moduleList=Module.objects.filter(group__parent_id=groupId).order_by('group__session','lesson')
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

def combingView(request, timetableId, groupByClass=True):
    if groupByClass=='False':
        groupByClass=False
    context={}
    timetable=Timetable.objects.get(id=timetableId)
    teachers=Teacher.objects.filter(department=timetable.tableYear.department).order_by('name')
    periods=Period.objects.filter(department=timetable.tableYear.department)
    groups=ModuleGroup.objects.filter(parent__timetable=timetable).order_by('name', 'session')
    classes=Module.objects.filter(group__parent__timetable=timetable)
    unassigned = False
    modules=[]
    parents=set()
    pAssign={}
    mJson={}
    index=1
    if not groupByClass:
        for period in periods:
            pAssign[period.dayNum]=period
    else:
        periods=list(periods)
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
    context['numWeeks']=timetable.tableYear.department.format.numWeeks
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
        classes=Module.objects.filter(teacher_id=teacher, group__parent__timetable_id=timetableId).order_by('name')
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
        classes=ModuleGroup.objects.filter(parent__timetable_id=timetableId).order_by('name')
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
    classes=ModuleGroup.objects.filter(parent__timetable_id=timetableId).order_by('name')
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


def cspTest(request, timetableA):
    from datetime import datetime
    now = datetime.now()
    tA=Timetable.objects.get(id=timetableA)
    timetable=createNewGeneratedTimetable(tA.tableYear, request.user, str(tA.tableYear.year) +"-"+now.strftime("%d%m%y"), tA)
    sched=getClassSchedule(timetable)
    if(not sched):
        return HttpResponse(status=502)
    teach=getTeacherDomains(timetable)
    try:
        csp1=CSP(sched, teach, timetable.tableYear.department.format.numWeeks)
    except ValueError as msg:
        timetable.delete()
        messages.error(request,str(msg))
        return redirect('dashboard')



    if csp1.checkPossible():
        count=0
        while count<3:
            if (csp1.assignTeacher()):
                for c, teacher in csp1.class_assignments.items():
                    Module.objects.filter(id=c).update(teacher_id=teacher)
                messages.success(request, f"New Timetable {timetable.name} has been generated")
                return redirect('dashboard')
            count+=1
        timetable.delete()
        messages.error(request, "No valid solution was found.")
        return redirect('dashboard')
    # return render(request, 'forms/timetableWizard.html', {'timetable':t})
    
def teacherPreferences(request, teacherId, timetableId):
    preferences=Preference.objects.filter(teacher_id=teacherId, module__group__parent__timetable_id=timetableId).order_by("module__group__parent","module__group__session")
    context={'preferences':preferences, 'teacherId':teacherId, 'timetableId':timetableId}
    return render(request, 'data/preferences.html', context)

def getGroups(request, parentId, combing=False):
    if not combing:
        groups=ModuleGroup.objects.filter(parent_id=parentId).order_by('session')
        choices=[(group.id, group.name) for group in groups]
    else:
        mods=Module.objects.filter(group__parent_id=parentId, teacher__isnull=True).order_by('lesson')
        choices = list(set(mods.values_list('group__id', 'group__name').distinct()))
    
    return JsonResponse({'choices':choices})

def getModulesJson(request, groupId, combing=False):
    if not combing:
        modules=Module.objects.filter(group_id=groupId).order_by('lesson')
    else:
        modules=Module.objects.filter(group_id=groupId, teacher__isnull=True).order_by('lesson')
    choices=[(mod.id, mod.name) for mod in modules]
    
    return JsonResponse({'choices':choices})

def departmentInfo(request, departmentId):
    department=Department.objects.get(id=departmentId)
    timetables=Timetable.objects.filter(tableYear__department=department)
    context={'department':department, 'timetables':timetables}
    return render(request, 'data/departmentInfo.html', context)

def exportCalendarView(request, timetableId, teacherId=None):
        timetable=Timetable.objects.get(id=timetableId)
        if teacherId:
            teacher=Teacher.objects.get(id=teacherId)
        else:
            teacher=None
        calendar=exportCalendar(timetable, teacher)
        response = HttpResponse(calendar,content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=calendar.xlsx'
        return response

def exportCombingView(request, timetableId):
    timetable=Timetable.objects.get(id=timetableId)
    chart=combingTemplateBuilder(timetable)
    response = HttpResponse(chart,content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=combing_chart.xlsx'
    return response
