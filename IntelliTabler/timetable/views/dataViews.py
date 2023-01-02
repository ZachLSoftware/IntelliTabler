from django.shortcuts import get_object_or_404, render, redirect
from ..models import Department, Teacher
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
    if(id):
        id=request.GET.get('id', 0)
        if(id):
            objects=Type.objects.filter(user=request.user, department_id=id)
    else:
        objects=Type.objects.filter(user=request.user)
    context['type']= type
    context["entities"]=objects
    context["objectId"]=id
    return render(request, "data/sideBarList.html", context)


def getTeacher(request, id):
    teacher=Teacher.objects.get(id=id)
    context={}
    context["teacher"]=teacher
    return render(request, "data/teacherInfo.html", context)
