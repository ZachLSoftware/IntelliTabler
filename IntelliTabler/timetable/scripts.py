from .models import ModuleGroup, Period
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
