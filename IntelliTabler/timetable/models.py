from django.db import models
from django.contrib.auth.models import AbstractUser
from django_random_id_model import RandomIDModel
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

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
        for count in range(1, totalPeriods+1):
            if(count%(instance.numPeriods*5)==0):
                week=int(count/(instance.numPeriods*5))
                i=1
            else:
                week=int(count/(instance.numPeriods*5))+1
            
            Period.objects.create(name=days[count%5]+str(round(i/5+.4)), dayNum=count, department=instance.department, week=week)
            i+=1
        '''
        for i in range(1,instance.numWeeks+1):
            for day in days:
                for j in range(1,instance.numPeriods+1):
                    Period.objects.create(name=day+str(j), dayNum=count, department=instance.department, week=i)
                    count+=1
        '''
    

class Teacher(RandomIDModel):
    name = models.CharField(max_length=50)
    totalHours = models.IntegerField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    roomNum = models.IntegerField(blank=True, null=True)
    department=models.ForeignKey(Department, on_delete=models.CASCADE)

class Availability(models.Model):
    period = models.CharField(max_length=20)
    week = models.IntegerField()
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

class Year(models.Model):
    YEARS=[]
    for i in range(datetime.datetime.now().year-10, datetime.datetime.now().year+10):
        YEARS.append((i,i))
    year=models.IntegerField(('year'), choices=YEARS, default=datetime.datetime.now().year)
    department=models.ForeignKey(Department, on_delete=models.CASCADE)

class ModuleGroup(models.Model):
    name=models.CharField(max_length=50)
    numPeriods=models.IntegerField()
    numClasses=models.IntegerField()
    department=models.ForeignKey(Department, on_delete=models.CASCADE)
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    year=models.ForeignKey(Year, on_delete=models.CASCADE)

class Module(models.Model):
    name=models.CharField(max_length=50)
    group=models.ForeignKey(ModuleGroup, on_delete=models.CASCADE)
    groupNum=models.IntegerField()
    Period=models.ForeignKey(Period, blank=True, null=True, on_delete=models.SET_NULL)
    Teacher=models.ForeignKey(Teacher, blank=True, null=True, on_delete=models.SET_NULL)

@receiver(post_save, sender=ModuleGroup)
def createModules(sender, instance, created, **kwargs):
    if created:
        for i in range(1, instance.numPeriods+1):
            for j in range(1, instance.numClasses+1):
                Module.objects.create(name=instance.name+"x"+str(j), group=instance, groupNum=i)
        

class Preference(models.Model):
    class Priority(models.IntegerChoices):
        REQUIRED=4
        HIGH=3
        MEDIUM=2
        NEUTRAL=1

    priority = models.IntegerField(choices=Priority.choices, default=Priority.NEUTRAL)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
