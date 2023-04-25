from __future__ import absolute_import, unicode_literals

from celery import shared_task
from .models import Timetable
from .helper_functions.csp import *
import json

@shared_task
def verifyTimetable(timetableId):
    timetable=Timetable.objects.get(id=timetableId)
    sched=getClassSchedule(timetable)
    if(not sched):
        error = {"error": "Some classes are not scheduled. Please ensure that all classes are scheduled."}
        return {"HX-Trigger": {'asyncResults': {"result":"danger","resultMsg": f"{timetable.name}: {error}", "id":verifyTimetable.request.id, "timetableId":timetableId}}}

    teach=getTeacherDomains(timetable)
    try:
        csp1=CSP(sched, teach, timetable.tableYear.department.format.numWeeks, verify=True)
    except ValueError as msg:
            return {"HX-Trigger": {'asyncResults': {"result":"danger","resultMsg": f"{timetable.name}: verification failed with {msg}", "id":verifyTimetable.request.id, "timetableId":timetableId}}}

    partial=len(Module.objects.filter(group__parent__timetable=timetable, teacher__isnull=True))>0
    assignments=Module.objects.filter(group__parent__timetable=timetable, teacher__isnull=False)
    verify=csp1.verifyAssignments(assignments)
    if not verify:
        if partial:
            return {"HX-Trigger": {'asyncResults': {"result":"danger","resultMsg": f"{timetable.name}: partial assignments made are invalid, please check them again.", "id":verifyTimetable.request.id, "timetableId":timetableId}}}
        else:
            return {"HX-Trigger": {'asyncResults': {"result":"danger","resultMsg": f"{timetable.name}: assignments made are invalid, please check them again.", "id":verifyTimetable.request.id, "timetableId":timetableId}}}
    else:
        if partial:
            return {"HX-Trigger": {'asyncResults': {'result':'success', 'resultMsg':f'{timetable.name}: partial assignments are currently valid.', "id":verifyTimetable.request.id, "timetableId":timetableId}}}
        else:
            return {"HX-Trigger": {'asyncResults': {'result':'success', 'resultMsg':f'{timetable.name}: assignments are valid.', "id":verifyTimetable.request.id, "timetableId":timetableId}}}


@shared_task
def autoAssign(timetableId):
    timetable=Timetable.objects.get(id=timetableId)
    #Get scheduled classes and check if all assigned to periods.
    sched=getClassSchedule(timetable)
    if(not sched):
        return {"HX-Trigger": {'asyncResults': {'result':'danger', 'resultMsg':f"{timetable.name} some classes are not scheduled. Assignment is not possible.", "id":autoAssign.request.id, "timetableId":timetableId}}}
    
    #Get Teachers for the domains
    teach=getTeacherDomains(timetable)

    #Try creating the CSP object, through errors into a message.
    #Possible errors include assignments from user preferences
    #that are not possible.
    try:
        csp1=CSP(sched, teach, timetable.tableYear.department.format.numWeeks)
    except ValueError as msg:
        return {"HX-Trigger": {'asyncResults': {'result':'danger', 'resultMsg':f"{timetable.name} assignment failed: {msg}", "id":autoAssign.request.id, "timetableId":timetableId}}}


    #Checks if there is enough teacher load to handle all classes
    try:
        csp1.checkPossible()
    except ValueError as msg:
        return {"HX-Trigger": {'asyncResults': {'result':'danger', 'resultMsg':f"{timetable.name} assignment failed: {msg}", "id":autoAssign.request.id, "timetableId":timetableId}}}


    #Tries up to 2 times to run the CSP incase of a bad initial assignment.
    count=0
    while count<2:

        #Run CSP
        if (csp1.assignTeacher()):

            #Save assignments as objects and return new timetable
            for c, teacher in csp1.class_assignments.items():
                Module.objects.filter(id=c).update(teacher_id=teacher)
            return {"HX-Trigger": {'asyncResults': {'result':'success', 'resultMsg':f"Timetable {timetable.name} has completed Auto Assignment successfully", "id":autoAssign.request.id, "timetableId":timetableId}}}

        csp1.repeatConstraint=False
        csp1.resetAssignments()
        csp1.setCurrDom()
        count+=1
    
    #If we haven't found a solution, delete timetable and return.
    return {"HX-Trigger": {'asyncResults': {'result':'success', 'resultMsg':f"Timetable {timetable.name} assignment was unsuccessful. Please verify teacher and class information.", "id":autoAssign.request.id, "timetableId":timetableId}}}
