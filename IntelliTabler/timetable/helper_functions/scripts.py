from ..models import ModuleGroup, Period, Timetable, Format
import json
from django.db.models import F
from .serializers import *

def updatePeriod(group, pName, week, manual=False):
    weeks=group.parent.department.format.numWeeks
    if group.parent.repeat or manual:
        weeks=group.parent.department.format.numWeeks
        sessions=group.parent.numPeriods
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
        obj.period=Period.objects.get(department=group.parent.department, name=pName, week=w)
        obj.save()
        module_ser=ModuleGroupSerializer(obj)
        module=module_ser.data
        module['groupid']=module_ser.data['id']
        update.append(module)
        w+=1
    return update
            # i=0
            # for week in range(1,weeks):
            #     if objs[i]==group:
            #         objs[i].processed=True
            #     objs[i].processed=True
            #     objs[i].period=Period.objects.get(department=group.parent.department, name=group.period.name, week=week)
            #     objs[i].save()
            #     del group.processed
            #     i+=1

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