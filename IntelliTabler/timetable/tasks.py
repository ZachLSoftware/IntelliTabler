from celery import shared_task
from .models import Timetable
from .helper_functions.csp import *
import json

"""
Task for verifying timetable assignments.
"""
@shared_task
def verifyTimetable(timetableId):

    #Try to get the timetable object, return error if not
    try:
        timetable=Timetable.objects.get(id=timetableId)
    except:
        error = "Error loading timetable object."
        return {"HX-Trigger": {'asyncResults': {"result":"danger","resultMsg": f"{timetable.name}: {error}", "id":verifyTimetable.request.id, "timetableId":timetableId}}}
    
    #Get Class Schedule and return if not scheduled
    sched=getClassSchedule(timetable)
    if(not sched):
        error = "Some classes are not scheduled. Please ensure that all classes are scheduled."
        return {"HX-Trigger": {'asyncResults': {"result":"danger","resultMsg": f"{timetable.name}: {error}", "id":verifyTimetable.request.id, "timetableId":timetableId}}}

    #Get teachers
    teach=getTeacherDomains(timetable)

    #Try to verify, catching errors if invalid data.
    try:
        csp1=CSP(sched, teach, timetable.tableYear.department.format.numWeeks, verify=True)
    except ValueError as msg:
            return {"HX-Trigger": {'asyncResults': {"result":"danger","resultMsg": f"{timetable.name}: verification failed with {msg}", "id":verifyTimetable.request.id, "timetableId":timetableId}}}

    #Check if this is a partial assignment
    partial=len(Module.objects.filter(group__parent__timetable=timetable, teacher__isnull=True))>0

    #Get current assigned classes
    assignments=Module.objects.filter(group__parent__timetable=timetable, teacher__isnull=False)
    
    #Try verify class assignments
    verify=csp1.verifyAssignments(assignments)

    #Return results.
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
    try:
        timetable=Timetable.objects.get(id=timetableId)
    except:
        return {"HX-Trigger": {'asyncResults': {'result':'danger', 'resultMsg':f"{timetable.name} assignment failed: Unable to get timetable object.", "id":autoAssign.request.id, "timetableId":timetableId}}}
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
        
        try:
            #Run CSP
            if (csp1.assignTeacher()):

                #Save assignments as objects and return new timetable
                for c, teacher in csp1.class_assignments.items():
                    Module.objects.filter(id=c).update(teacher_id=teacher)
                return {"HX-Trigger": {'asyncResults': {'result':'success', 'resultMsg':f"Timetable {timetable.name} has completed Auto Assignment successfully", "id":autoAssign.request.id, "timetableId":timetableId}}}

            #Remove repeat constraint to allow for more options.
            csp1.repeatConstraint=False

            #Reset domains and assignments
            csp1.resetAssignments()
            csp1.setCurrDom()
            count+=1
        except:
            return {"HX-Trigger": {'asyncResults': {'result':'danger', 'resultMsg':f"Timetable {timetable.name}: Unknown error. Task aborted.", "id":autoAssign.request.id, "timetableId":timetableId}}}
    
    #If we haven't found a solution, delete timetable and return.
    return {"HX-Trigger": {'asyncResults': {'result':'danger', 'resultMsg':f"Timetable {timetable.name} assignment was unsuccessful. Please verify teacher and class information.", "id":autoAssign.request.id, "timetableId":timetableId}}}
