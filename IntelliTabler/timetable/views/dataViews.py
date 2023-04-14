from django.shortcuts import get_object_or_404, render, redirect
from ..models import Department, Teacher, Module, ModuleGroup, Timetable, Period, ModuleParent, Format, Year
from django.contrib.auth.decorators import login_required
from django.apps import apps
import json
from django.http import JsonResponse
from ..helper_functions.serializers import *
from ..helper_functions.csp import *
from django.http import HttpResponse
from django.contrib import messages
from ..helper_functions.toExcel import *
from ..helper_functions.scripts import getCalendar


###Default Landing Page###
def index(request):
    return redirect('dashboard')


"""
dashboard gets all departments from the user and creates a dictionary
with years as their values.
"""
@login_required
def dashboard(request):
    context={}

    #Get Departments based on user and create dictionary for dropdowns
    ds=Department.objects.filter(user=request.user).order_by('name')
    context['departments']={d:Year.objects.filter(department_id=d.id).order_by('year') for d in ds}
    context['template']="dashboard_"+request.user.theme+".html"
    timetableId=request.session.get('timetableId', 0)
    if timetableId:
        table=get_object_or_404(Timetable, pk=timetableId)
        context['departmentTitle']=table.tableYear.department.name +" "+ str(table.tableYear.year)
        del request.session['timetableId']
    else:
        context['departmentTitle']=0
    context['timetableId']=timetableId
    return render(request, "dashboard.html", context)

"""
Sets the current timetable and gets all available timetables for the year.
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


"""
Gets necessary elements to display on the timetable information page.
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

"""
getList gets a type and the current timetableId.
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

"""
Recieves type of object and timetable.
Returns the sidebar template page with either
teacher or module objects in a list.
"""
def getSidebar(request, type, timetableId):
    timetable=Timetable.objects.get(id=timetableId)

    #Fill in necessary object details
    context={
        'type':type, 
        'infoType': type,
        'timetable': timetable,
        'detailPath': 'getTeacher',
    }

    #Special details for modules
    if type.upper()=='MODULEPARENT':
        context['infoType']='module'
        context['detailPath']='getModules'
    return render(request, 'data/sidebarTemplate.html', context)

"""
Accepts a teacher Id and a timetable Id.
Gets the teachers assigned modules, and the teacher object.
Returns an organized dictionary of classes, with the parent as the key
"""
def getTeacher(request, id, timetableId):

    #Try to get the teacher object or return 404
    teacher=get_object_or_404(Teacher, pk=id)

    #Get any modules that are assigned to the teacher in this timetable
    mods=Module.objects.filter(teacher=teacher, group__parent__timetable_id=timetableId).order_by('name', 'group__period')
    parents=ModuleParent.objects.filter(timetable_id=timetableId).order_by('name')
    
    #Use dictionary and list comprehension to sort modules into lists with the parent as the key
    #Used for drop down organization in teacher info.
    modules={key: [mod for mod in mods if mod.group.parent==key] for key in parents if any(mod.group.parent == key for mod in mods)}

    context={}
    context['modules']=modules
    context["teacher"]=teacher
    context["timetableId"]=timetableId
    return render(request, "data/teacherInfo.html", context)


def getModules(request, groupId, timetableId=0):

    #Checks if the requesting page is a calendar
    calendar=request.GET.get('calendar',0)

    #If calendar, we are getting the modules based on group else, we are getting from parent
    if calendar:
        moduleList=Module.objects.filter(group_id=groupId).order_by('lesson')
    else:      
        moduleList=Module.objects.filter(group__parent_id=groupId).order_by('group__session','lesson')
    context={}

    #Dictionary Comprehension to group modules by group
    modules={}
    modules = {mod.group: [m for m in moduleList if m.group == mod.group] for mod in moduleList if mod.group not in modules}
    context["modules"]=modules
    context["parent"]=moduleList[0].group.parent
    context["group"]=groupId
    return render(request, "data/modulesInfo.html", context)

def combingView(request, timetableId, groupByClass=True):

    #If user has requested group by period
    if groupByClass=='False':
        groupByClass=False

    context={}
    
    #Trye to get timetable, return 404 if else
    timetable=get_object_or_404(Timetable, pk=timetableId)

    #Get details requred for chart
    teachers=Teacher.objects.filter(department=timetable.tableYear.department).order_by('name')
    periods=Period.objects.filter(department=timetable.tableYear.department)
    groups=ModuleGroup.objects.filter(parent__timetable=timetable).order_by('name', 'session')
    classes=Module.objects.filter(group__parent__timetable=timetable)
    parents=ModuleParent.objects.filter(timetable=timetable)
    context['timetableId']=timetableId
    context['numWeeks']=timetable.tableYear.department.format.numWeeks
    context['teachers']=teachers
    context['parents']=parents
    
    #Set flag to check if some classes aren't assigned a time slot.
    unassigned = len(Module.objects.filter(group__parent__timetable=timetable, group__period__isnull=True))>0
    context['unassigned']=unassigned

    if not unassigned:
        #Set items
        modules=[]
        pAssign={}
        mJson={}
        index=1

        #If user sorts by period
        if not groupByClass:
            pAssign={period.dayNum:period for period in periods}

        #Creates a dictionary of periods by index sorted so classes are
        #grouped as closely as possible.
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
        

        #Loop through classes and retrieve necessary details
        #Not using list or dictionary comprehension as multiple steps are required per class
        for cl in classes:
            
            #Creates a key with an empty list if key doesn't exist, and appends to that list
            mJson.setdefault(cl.group.id, []).append((cl.id, cl.name))

            #If the class has been assigned a teacher, get details
            if cl.teacher:
                #Serialize class ready to add to chart
                module_ser=ModuleSerializer(cl)
                module=module_ser.data
                #Create the session id (allows for correct placement on chart)
                module["session"]="#" + str(cl.teacher.id) +"x" + cl.group.period.name + "-"+ str(cl.group.period.week)
                module["teacher"]=cl.teacher.id
                modules.append(module)
        
        #Set items ready for adding ot the chart
        context['modules']=json.dumps(modules)
        context['periods']=pAssign
        context['numPeriods']=len(periods)
        context['modChoices']=json.dumps(mJson)
    return render(request, 'data/combingView.html', context)


"""
Accepts a timetable id and teacher. If teacher, modules are the teachers assigned classes.
Returns details to build the calendar.
"""
def calendarView(request, timetableId, teacherId=0):
    t=get_object_or_404(Timetable, pk=timetableId)

    #If Teacher, set title
    if teacherId:
        teacher=get_object_or_404(Teacher, pk=teacherId)
        title=teacher.name + " - "   + t.tableYear.department.name + " - "+ str(t.name)
    else:
       title = t.tableYear.department.name + " - " + str(t.name)
    
    #Get calendar data
    context=getCalendar(timetableId, teacherId)
    context['title']=title
    return render(request, 'data/calendarView.html', context)

"""CHECK IF NEEDED"""
# def getCalendarData(timetableId):
#     classes=ModuleGroup.objects.filter(parent__timetable_id=timetableId).order_by('name')
#     events={}
#     modules=[]
#     for cl in classes:
#         if cl.period:
#             module_ser=ModuleGroupSerializer(cl)
#             module=module_ser.data
#             module['groupid']=module_ser.data['id']
#             modules.append(module)
#     events["modules"]=modules
#     context={}
#     context['events']=events
#     return JsonResponse(events)


"""
Auto Assignment function. 
Accepts a timetable and returns a copy with assignments made if possible.
"""
def cspAutoAssign(request, timetableA):
    #Get date time for naming generated Timetable
    from datetime import datetime
    now = datetime.now()
    tA=Timetable.objects.get(id=timetableA)

    #Get 4 characters from uuid to mark a timetable unique
    uniqueId = uuid.uuid4().hex[:4]
    timetable=createNewGeneratedTimetable(tA.tableYear, str(tA.tableYear.year) +" - "+now.strftime("%d/%m") + " - " + str(uniqueId), tA)
    
    #Get scheduled classes and check if all assigned to periods.
    sched=getClassSchedule(timetable)
    if(not sched):
        timetable.delete()
        messages.error(request,str("Some classes are not scheduled. Assignment is not possible."))
        return redirect('dashboard')
    
    #Get Teachers for the domains
    teach=getTeacherDomains(timetable)

    #Try creating the CSP object, through errors into a message.
    #Possible errors include assignments from user preferences
    #that are not possible.
    try:
        csp1=CSP(sched, teach, timetable.tableYear.department.format.numWeeks)
    except ValueError as msg:
        timetable.delete()
        messages.error(request,str(msg))
        return redirect('dashboard')

    #Checks if there is enough teacher load to handle all classes
    if csp1.checkPossible():

        #Tries up to 3 times to run the CSP incase of a bad initial assignment.
        count=0
        while count<3:

            #Run CSP
            if (csp1.assignTeacher()):

                #Save assignments as objects and return new timetable
                for c, teacher in csp1.class_assignments.items():
                    Module.objects.filter(id=c).update(teacher_id=teacher)
                messages.success(request, f"New Timetable {timetable.name} has been generated")
                request.session['timetableId']=timetable.id
                return redirect('dashboard')
            count+=1
        
        #If we haven't found a solution, delete timetable and return.
        timetable.delete()
        messages.error(request, "No valid solution was found.")
        return redirect('dashboard')

"""
Returns list of preferences for a teacher.
"""
def teacherPreferences(request, teacherId, timetableId):
    preferences=Preference.objects.filter(teacher_id=teacherId, module__group__parent__timetable_id=timetableId).order_by("module__group__parent","module__group__session")
    context={'preferences':preferences, 'teacherId':teacherId, 'timetableId':timetableId}
    return render(request, 'data/teacherPreferences.html', context)

def preferences(request, timetableId):
    timetable=get_object_or_404(Timetable, id=timetableId)
    teachers=Teacher.objects.filter(department=timetable.tableYear.department).order_by('name')
    preferences={}
    for teacher in teachers:
        preferences[teacher]=Preference.objects.filter(timetable=timetable, teacher=teacher).order_by("module__group__parent","module__group__session")
    context={'timetable':timetable, 'preferences':preferences}
    return render(request, 'data/preferences.html', context)

"""
Returns modules for use in dropdown menues
"""
def getGroups(request, parentId, combing=False):
    #Checks if choice is from the combing chart
    if not combing:
        groups=ModuleGroup.objects.filter(parent_id=parentId).order_by('session')
        choices=[(group.id, group.name) for group in groups]
    else:
        mods=Module.objects.filter(group__parent_id=parentId, teacher__isnull=True).order_by('lesson')
        choices = list(set(mods.values_list('group__id', 'group__name').distinct()))
    
    return JsonResponse({'choices':choices})

"""
returns a json of module choices
"""
def getModulesJson(request, groupId, combing=False):
    if not combing:
        modules=Module.objects.filter(group_id=groupId).order_by('lesson')
    else:
        modules=Module.objects.filter(group_id=groupId, teacher__isnull=True).order_by('lesson')
    choices=[(mod.id, mod.name) for mod in modules]
    
    return JsonResponse({'choices':choices})

"""
Returns department information.
"""
def departmentInfo(request, departmentId):
    department=Department.objects.get(id=departmentId)
    #timetables=Timetable.objects.filter(tableYear__department=department)
    context={'department':department}
    return render(request, 'data/departmentInfo.html', context)


"""
Export view for calendar
"""
def exportCalendarView(request, timetableId, teacherId=None):
        
        timetable=Timetable.objects.get(id=timetableId)

        #If teacher, then we get teacher and get calendar events based on teacher assignments
        if teacherId:
            teacher=Teacher.objects.get(id=teacherId)
        else:
            teacher=None

        #Call export function from toExcel.py 
        calendar=exportCalendar(timetable, teacher)

        #Return httpresponse that allows for a download
        response = HttpResponse(calendar,content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=calendar.xlsx'
        return response

"""
Export the combing chart to excel
"""
def exportCombingView(request, timetableId):
    timetable=Timetable.objects.get(id=timetableId)

    #Call combing chart export
    chart=combingTemplateBuilder(timetable)

    #Return downloadable httpresponse
    response = HttpResponse(chart,content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=combing_chart.xlsx'
    return response
