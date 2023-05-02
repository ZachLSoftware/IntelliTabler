from ..models import ModuleGroup, Period, Timetable, Format
import json
from django.db.models import F
from .serializers import *

"""
Update period for the calendar app. 
Serializes and packages the update.
"""
def updatePeriod(group, pName, week, manual=False):
    weeks=group.parent.department.format.numWeeks
    #If set to repeat get other periods necessary
    if group.parent.repeat or manual:
        weeks=group.parent.department.format.numWeeks
        sessions=group.parent.numPeriods

        #Get module groups based on the modulo calculation of sessions/weeks
        #Objects found based on if the modulos calculation is equal to the target.
        modu=sessions/weeks
        modu=int(modu)
        target=group.session%modu
        objs=ModuleGroup.objects.annotate(mod=F('session') % modu).filter(parent=group.parent, mod=target).order_by('session')
        w=1
    else:
        objs=[group]
        w=int(week)
    update=[]
    for obj in objs:
        #Update the object with the period assigned
        obj.period=Period.objects.get(department=group.parent.department, name=pName, week=w)
        obj.save()
        
        #Serialize the group and add to the update list
        module_ser=ModuleGroupSerializer(obj)
        module=module_ser.data
        module['groupid']=module_ser.data['id']
        update.append(module)
        w+=1
    return update
            

"""Special Function to help get all data for the calendar in a serialized format."""
def getCalendar(timetableId, teacherId=0):
    events={}
    modules=[]
    context={}
    if teacherId:
        classes=Module.objects.filter(teacher_id=teacherId, group__parent__timetable_id=timetableId).order_by('name')
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
    context['teacherId']=teacherId
    return context