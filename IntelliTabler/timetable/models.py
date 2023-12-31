from django.db import models
from django.contrib.auth.models import AbstractUser
from django_random_id_model import RandomIDModel
import uuid
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import datetime
from django.utils.translation import gettext_lazy as _

"""
Custom User Class
"""
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

class Period(models.Model):
    name = models.CharField(max_length=50)
    dayNum = models.IntegerField()
    week = models.IntegerField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

class Teacher(RandomIDModel):
    name = models.CharField(max_length=50)
    load = models.IntegerField(blank=True, null=True)
    roomNum = models.CharField(max_length=20, blank=True, null=True)
    department=models.ForeignKey(Department, on_delete=models.CASCADE)

class Availability(models.Model):
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

class Year(RandomIDModel):

    #Create dropdown for years with 5 years on either side of the current year
    YEARS=[]
    for i in range(datetime.datetime.now().year-5, datetime.datetime.now().year+5):
        YEARS.append((i,i))

    #Set default year to current year.
    year=models.IntegerField(('year'), choices=YEARS, default=datetime.datetime.now().year)
    department=models.ForeignKey(Department, on_delete=models.CASCADE)
    defaultTimetable=models.OneToOneField('Timetable', null=True, on_delete=models.SET_NULL)

class Timetable(RandomIDModel):
    name = models.CharField(max_length=40)
    tableYear = models.ForeignKey(Year, on_delete=models.CASCADE)
    generating = models.BooleanField(default=False)
    taskId = models.CharField(max_length=100, null=True)
    latestMsg=models.CharField(max_length=150, null=True)
    
class ModuleParent(RandomIDModel):
    name=models.CharField(max_length=50)
    sharedId=models.CharField(max_length=36, default=uuid.uuid4)
    numPeriods=models.IntegerField()
    numClasses=models.IntegerField()
    department=models.ForeignKey(Department, on_delete=models.CASCADE)
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
    lessonNum = models.IntegerField()

class Preference(models.Model):
    class Priority(models.IntegerChoices):
        REQUIRED=3
        HIGH=2
        MEDIUM=1
        NONE=0

    priority = models.IntegerField(choices=Priority.choices, default=Priority.NONE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE)


"""
Create year instance on dpeartment save.
"""
@receiver(post_save, sender=Department)
def createDefaultYear(sender, instance, created, **kwargs):
    if created:
        Year.objects.create(department=instance)

"""
Create a default timetable. This is the actual table that manipulates modules
Other timetables created won't affect the actual modules and are for making theoretical tables
"""
@receiver(post_save, sender=Year)
def defaultTimetable(sender, instance, created, **kwargs):
    if created:
        t=Timetable.objects.create(name=str(instance.year)+" Timetable", tableYear=instance)
        instance.defaultTimetable=t
        instance.save()

"""
When a format is saved, automatically create the periods.
"""
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

"""
If a format is changed, update periods.
"""
@receiver(pre_save, sender=Format)
def editPeriods(sender, instance, **kwargs):

    #Check if format exists and isn't being created.
    oldFormat=Format.objects.filter(department=instance.department).first()
    if not instance._state.adding and oldFormat:

        #If adding periods, check if a period exists, if not create, else update the period number
        if oldFormat.numPeriods<instance.numPeriods:
            days=["Fri-","Mon-","Tues-","Wed-","Thurs-"]
            totalPeriods=instance.numPeriods*5*oldFormat.numWeeks
            i=1
            week=1
            for count in range(1, totalPeriods+1):
                if not Period.objects.filter(name=days[count%5]+str(round(i/5+.4)), department=instance.department, week=week).exists():
                    Period.objects.create(name=days[count%5]+str(round(i/5+.4)), dayNum=count, department=instance.department, week=week)
                else:
                    Period.objects.filter(name=days[count%5]+str(round(i/5+.4)), department=instance.department, week=week).update(dayNum=count)
                i+=1
                if(count%(instance.numPeriods*5)==0):
                    week+=1
                    i=1
        
        #If adding weeks, add periods at the end of current period range
        if oldFormat.numWeeks<instance.numWeeks:
            days=["Fri-","Mon-","Tues-","Wed-","Thurs-"]
            totalPeriods=instance.numPeriods*5*instance.numWeeks
            starting=oldFormat.numPeriods*5*oldFormat.numWeeks
            i=1
            week=oldFormat.numWeeks+1
            for count in range(starting+1, totalPeriods+1):
                Period.objects.create(name=days[count%5]+str(round(i/5+.4)), dayNum=count, department=instance.department, week=week)
                i+=1
                if(count%(instance.numPeriods*5)==0):
                    week+=1
                    i=1

        #If reducing weeks, delete periods in trailing weeks.
        if oldFormat.numWeeks>instance.numWeeks:
            periods=Period.objects.filter(department=instance.department, week__gt=instance.numWeeks)
            for period in periods:
                period.delete()

        #If reducing periods, delete trailing periods for each week, and reset dayNum variables
        if oldFormat.numPeriods>instance.numPeriods:
            count=1
            periods=Period.objects.filter(department=instance.department).order_by('dayNum')
            for period in periods:
                if int(period.name.split('-')[1])>instance.numPeriods:
                    period.delete()
                else:
                    period.dayNum=count
                    period.save()
                    count+=1


"""
Create modulegroups and modules based on moduleparent.
"""
@receiver(post_save, sender=ModuleParent)
def createModules(sender, instance, created, **kwargs):
    if created:
        #module sharedkey dictionary to track sharedkeys
        mSharedKey={}
        lessonNum=1

        #Create Module Groups for each period
        for i in range(1, instance.numPeriods+1):
            group = ModuleGroup.objects.create(name=instance.name+" Lesson " + str(i), parent=instance, session=i)

            #Create lesson group for each class
            for j in range(1, instance.numClasses+1):

                #If this is the first group, save all the sharedkeys to dictionary
                if i==1:
                    mod = Module.objects.create(name=instance.name+"-"+str(j), lesson=j, lessonNum=lessonNum, group=group)
                    mSharedKey[j]=mod.sharedKey
                else:
                    mod = Module.objects.create(name=instance.name+"-"+str(j), lesson=j, lessonNum=lessonNum, group=group, sharedKey=mSharedKey[j])
                lessonNum+=1
  
"""
Update Modules when a ModuleParent is updated.
"""
@receiver(pre_save, sender=ModuleParent)
def updateModuleParent(sender, instance, **kwargs):
    #Check if instance exists and is not being added(created)
    if not instance._state.adding and ModuleParent.objects.filter(id=instance.id).exists():

        #Get current instance before update
        oldInstance=ModuleParent.objects.get(id=instance.id)

        #If new instance has less periods, delete trailing module groups.
        if oldInstance.numPeriods>instance.numPeriods:
            for mod in ModuleGroup.objects.filter(parent=oldInstance, session__gt=instance.numPeriods):
                if mod.session > instance.numPeriods:
                    mod.delete()

        #If new instance has less classes, delete trailing classes based on lesson number
        if oldInstance.numClasses>instance.numClasses:
            for mod in Module.objects.filter(group__parent=oldInstance, lesson__gt=instance.numClasses):
                if mod.lesson>instance.numClasses:
                    mod.delete()

        #Create sharedkey dict and get current sharedkeys
        mSharedKey={}
        g=ModuleGroup.objects.filter(parent=oldInstance).order_by('session').first()
        for mod in Module.objects.filter(group=g):
            mSharedKey[mod.lesson]=mod.sharedKey
        
        #Add classes with new sharedkeys,
        if oldInstance.numClasses<instance.numClasses:
            groups = ModuleGroup.objects.filter(parent=oldInstance, session__lte=instance.numPeriods)
            i=1
            for group in groups:
                for j in range(oldInstance.numClasses+1, instance.numClasses+1):
                    if j not in mSharedKey.keys():
                        mod = Module.objects.create(name=instance.name+"-"+str(j), lessonNum=1, lesson=j, group=group)
                        mSharedKey[j]=mod.sharedKey
                    else:
                        mod = Module.objects.create(name=instance.name+"-"+str(j), lessonNum=1, lesson=j, group=group, sharedKey=mSharedKey[j])

                i+=1
            
            #Reset lesson numbers and update modules
            lessonNum=1
            mods=Module.objects.filter(group__parent_id=instance.id).order_by('group','group__session', 'lesson')
            for mod in mods:
                mod.lessonNum=lessonNum
                lessonNum+=1
                mod.save()

        #Add new periods and classes. This is done after adding classes.
        if oldInstance.numPeriods<instance.numPeriods:
            lessonNum=oldInstance.numPeriods*oldInstance.numClasses+1
            for i in range(oldInstance.numPeriods+1, instance.numPeriods+1):
                group = ModuleGroup.objects.create(name=instance.name+" Lesson " + str(i), parent=instance, session=i)
                for j in range(1, instance.numClasses+1):
                    mod=Module.objects.create(name=instance.name+"-"+str(j), lessonNum=lessonNum, lesson=j, group=group)
                    mSharedKey[j]=mod.sharedKey
                    lessonNum+=1

        #If the name has changed, update each modulegroup and module with the new name
        if oldInstance.name!=instance.name:
            group=ModuleGroup.objects.filter(parent=oldInstance)
            for g in group:
                split=g.name.split(" Lesson ")
                g.name=instance.name+ "  Lesson " + str(g.session)
                g.save()
                for module in Module.objects.filter(group=g):
                    suffix=module.name.split(oldInstance.name)
                    module.name=instance.name+suffix[1]
                    module.save()

        #If repeat changes, update module period assignments accordingly
        if oldInstance.repeat!=instance.repeat:
            if instance.repeat:
                sessions=instance.numPeriods/oldInstance.timetable.tableYear.department.format.numWeeks
                groups=ModuleGroup.objects.filter(parent=oldInstance).filter(session__lte=sessions).order_by('session')
                for group in groups:
                    if group.period:
                        from .helper_functions.scripts import updatePeriod
                        updatePeriod(group, group.period.name, group.period.week, True)

"""
If a new timetable is created, clone any existing modules.
"""
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



