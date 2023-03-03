from django.db import models
from django.contrib.auth.models import AbstractUser
from django_random_id_model import RandomIDModel
import uuid
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import datetime
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import F
from django.db.models import Q
# from .scripts import updatePeriod


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    theme = models.CharField(max_length=5, default="light")

class Department(RandomIDModel):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

class Format(models.Model):
    numPeriods=models.IntegerField()
    numWeeks=models.IntegerField()
    department=models.OneToOneField(Department, on_delete=models.CASCADE, primary_key=True)

@receiver(post_save, sender=Department)
def createDefaultYear(sender, instance, created, **kwargs):
    if created:
        Year.objects.create(department=instance)

class Period(models.Model):
    name = models.CharField(max_length=50)
    dayNum = models.IntegerField()
    week = models.IntegerField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

@receiver(post_save, sender=Format)
def createPeriods(sender, instance, created, **kwargs):
    if created:
        days=["Fri-","Mon-","Tues-","Wed-","Thurs-"]
        totalPeriods=instance.numPeriods*5*instance.numWeeks
        i=1
        week=1
        for count in range(1, totalPeriods+1):

          
            Period.objects.create(name=days[count%5]+str(round(i/5+.4)), dayNum=count, department=instance.department, week=week)
            i+=1
            if(count%(instance.numPeriods*5)==0):
                week+=1
                i=1
            
        '''
        for i in range(1,instance.numWeeks+1):
            for day in days:
                for j in range(1,instance.numPeriods+1):
                    Period.objects.create(name=day+str(j), dayNum=count, department=instance.department, week=i)
                    count+=1
        '''
    

class Teacher(RandomIDModel):
    name = models.CharField(max_length=50)
    load = models.IntegerField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    roomNum = models.CharField(max_length=20, blank=True, null=True)
    department=models.ForeignKey(Department, on_delete=models.CASCADE)

class Availability(models.Model):
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    #week = models.IntegerField()
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

class Year(RandomIDModel):
    YEARS=[]
    for i in range(datetime.datetime.now().year-10, datetime.datetime.now().year+10):
        YEARS.append((i,i))
    year=models.IntegerField(('year'), choices=YEARS, default=datetime.datetime.now().year)
    department=models.ForeignKey(Department, on_delete=models.CASCADE)
    defaultTimetable=models.OneToOneField('Timetable', null=True, on_delete=models.SET_NULL)

#Create a default timetable. This is the actual table that manipulates modules
#Other timetables created won't affect the actual modules and are for making theoretical tables
@receiver(post_save, sender=Year)
def defaultTimetable(sender, instance, created, **kwargs):
    if created:
        t=Timetable.objects.create(user=instance.department.user, name=str(instance.year)+" Timetable", tableYear=instance)
        instance.defaultTimetable=t
        instance.save()

class Timetable(RandomIDModel):
    name = models.CharField(max_length=40)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tableYear = models.ForeignKey(Year, on_delete=models.CASCADE)
    
class ModuleParent(RandomIDModel):
    name=models.CharField(max_length=50)
    sharedId=models.CharField(max_length=36, default=uuid.uuid4)
    numPeriods=models.IntegerField()
    numClasses=models.IntegerField()
    department=models.ForeignKey(Department, on_delete=models.CASCADE)
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    timetable=models.ForeignKey(Timetable, on_delete=models.CASCADE)
    color=models.CharField(max_length=7, default="#0275d8")
    repeat=models.BooleanField(null=True, blank=True, default=False)

class ModuleGroup(RandomIDModel):
    name=models.CharField(max_length=50)
    period=models.ForeignKey(Period, blank=True, null=True, on_delete=models.SET_NULL)
    parent=models.ForeignKey(ModuleParent, on_delete=models.CASCADE)
    session=models.IntegerField()

class Module(RandomIDModel):
    name=models.CharField(max_length=50)
    lesson=models.IntegerField()
    group=models.ForeignKey(ModuleGroup, on_delete=models.CASCADE)
    teacher=models.ForeignKey(Teacher, blank=True, null=True, on_delete=models.SET_NULL)
    sharedKey=models.CharField(max_length=36, default=uuid.uuid4)

# class TimetableRow(models.Model):
#     timetable=models.ForeignKey(Timetable, on_delete=models.CASCADE)
#     module=models.ForeignKey(Module, on_delete=models.CASCADE)
#     manualTeacher=models.ForeignKey(Teacher, null=True, blank=True, on_delete=models.SET_NULL)
#     manualPeriod=models.ForeignKey(Period, null=True, on_delete=models.SET_NULL)

@receiver(post_save, sender=ModuleParent)
def createModules(sender, instance, created, **kwargs):
    if created:
        try:
            timetable=Timetable.objects.get(id=instance.department.id*instance.tableYear.year)
        except:
            timetable=None
        mSharedKey={}
        for i in range(1, instance.numPeriods+1):
            group = ModuleGroup.objects.create(name=instance.name+" Lesson " + str(i), parent=instance, session=i)
            for j in range(1, instance.numClasses+1):
                if i==1:
                    mod = Module.objects.create(name=instance.name+"-"+str(j), lesson=j, group=group)
                    mSharedKey[j]=mod.sharedKey
                else:
                    mod = Module.objects.create(name=instance.name+"-"+str(j), lesson=j, group=group, sharedKey=mSharedKey[j])
                

                # if timetable is not None:
                #     TimetableRow.objects.create(timetable=timetable, module=mod)
    # else:
    #     test=kwargs['update_fields']
    #     print(test)
        # groups=ModuleGroup.objects.filter(parent=instance.id).order_by('session')
        # if len(groups)>instance.numPeriods:
        #     for group in groups:
        #         if group.session > instance.numPeriods:
        #             group.delete()
        #         else:
        #             mods=Module.objects.filter(group=group)
        #             for mod in mods:
        #                 if int(mod.name.split("-")[1])> instance.numClasses:
        #                     mod.delete()

@receiver(pre_save, sender=ModuleParent)
def updateModuleParent(sender, instance, **kwargs):
    if not instance._state.adding and ModuleParent.objects.filter(id=instance.id).exists():
        oldInstance=ModuleParent.objects.get(id=instance.id)
        if oldInstance.numPeriods>instance.numPeriods:
            for mod in ModuleGroup.objects.filter(parent=oldInstance, session__gt=instance.numPeriods):
                if mod.session > instance.numPeriods:
                    mod.delete()
        if oldInstance.numClasses>instance.numClasses:
            for mod in Module.objects.filter(group__parent=oldInstance, lesson__gt=instance.numClasses):
                if mod.lesson>instance.numClasses:
                    mod.delete()
        mSharedKey={}
        g=ModuleGroup.objects.filter(parent=oldInstance).order_by('session').first()
        for mod in Module.objects.filter(group=g):
            mSharedKey[mod.lesson]=mod.sharedKey
        if oldInstance.numClasses<instance.numClasses:
            groups = ModuleGroup.objects.filter(parent=oldInstance, session__lte=instance.numPeriods)
            i=1
            for group in groups:
                for j in range(oldInstance.numClasses+1, instance.numClasses+1):
                    if j not in mSharedKey.keys():
                        mod = Module.objects.create(name=instance.name+"-"+str(j), lesson=j, group=group)
                        mSharedKey[j]=mod.sharedKey
                    else:
                        mod = Module.objects.create(name=instance.name+"-"+str(j), lesson=j, group=group, sharedKey=mSharedKey[j])

                i+=1
        if oldInstance.numPeriods<instance.numPeriods:
            for i in range(oldInstance.numPeriods+1, instance.numPeriods+1):
                group = ModuleGroup.objects.create(name=instance.name+" Lesson " + str(i), parent=instance, session=i)
                for j in range(1, instance.numClasses+1):
                    mod=Module.objects.create(name=instance.name+"-"+str(j), lesson=j, group=group)
                    mSharedKey[j]=mod.sharedKey
        if oldInstance.name!=instance.name:
            group=ModuleGroup.objects.filter(parent=oldInstance)
            for g in group:
                split=g.name.split()
                g.name=instance.name+ " " + split[1] + " " + split[2]
                g.save()
        if oldInstance.repeat!=instance.repeat:
            if instance.repeat:
                sessions=instance.numPeriods/oldInstance.timetable.tableYear.department.format.numWeeks
                groups=ModuleGroup.objects.filter(parent=oldInstance).filter(session__lte=sessions).order_by('session')
                for group in groups:
                    if group.period:
                        from .scripts import updatePeriod
                        updatePeriod(group, group.period.name, group.period.week, True)

            
@receiver(post_save, sender=Timetable)
def cloneModules(sender, instance, created, **kwargs):
    if created:
        sharedIds=ModuleParent.objects.filter(timetable__tableYear=instance.tableYear).values('sharedId').distinct()
        modules=[]
        for sid in sharedIds:
            m=ModuleParent.objects.filter(sharedId=sid['sharedId']).first()
            modules.append(m)
        for mod in modules:
            mod.pk=None
            mod.timetable=instance
            mod.save()

# @receiver(post_save, sender=Module)
# def updateRow(sender, instance, created, **kwargs):
#     if not created:
#         try:
#             timetable=Timetable.objects.get(id=instance.group.department.id*instance.group.year.year)
#             row=TimetableRow.objects.get(module=instance, timetable=timetable)
#         except:
#             return
#         row.manualTeacher=instance.teacher
#         row.manualPeriod=instance.period
#         row.save()

class Preference(models.Model):
    class Priority(models.IntegerChoices):
        REQUIRED=4
        HIGH=3
        MEDIUM=2
        NEUTRAL=1

    priority = models.IntegerField(choices=Priority.choices, default=Priority.NEUTRAL)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)


