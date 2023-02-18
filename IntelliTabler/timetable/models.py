from django.db import models
from django.contrib.auth.models import AbstractUser
from django_random_id_model import RandomIDModel
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


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
    period = models.CharField(max_length=20)
    week = models.IntegerField()
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
    name = models.CharField(max_length=20)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tableYear = models.ForeignKey(Year, on_delete=models.CASCADE)
    
class ModuleParent(RandomIDModel):
    name=models.CharField(max_length=50)
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

class Module(RandomIDModel):
    name=models.CharField(max_length=50)
    group=models.ForeignKey(ModuleGroup, on_delete=models.CASCADE)
    teacher=models.ForeignKey(Teacher, blank=True, null=True, on_delete=models.SET_NULL)

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
        for i in range(1, instance.numPeriods+1):
            group = ModuleGroup.objects.create(name=instance.name+" Lesson " + str(i), parent=instance)
            for j in range(1, instance.numClasses+1):
                mod = Module.objects.create(name=instance.name+"-"+str(j), group=group)
                # if timetable is not None:
                #     TimetableRow.objects.create(timetable=timetable, module=mod)

@receiver(post_save, sender=Timetable)
def cloneModules(sender, instance, created, **kwargs):
    if created:
        modules=ModuleParent.objects.filter(timetable__year=instance.tableYear)
        for mod in modules:
            mod.pk=None
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
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
