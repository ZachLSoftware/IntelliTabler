from .models import *

def createNewGeneratedTimetable(year, user, name, timetableA):
    t=Timetable.objects.create(name=name, tableYear=year, user=user)
    mgA=ModuleGroup.objects.filter(parent__timetable=timetableA)
    mgB=ModuleGroup.objects.filter(parent__timetable=t)
    for i in range(len(mgB)):
        mgB[i].period=mgA[i].period
        mgB[i].save()
    return t

def getClassSchedule(timetable):
    modules=Module.objects.filter(group__parent__timetable=timetable).order_by('group', 'name')
    schedule={}
    for mod in modules:
        schedule[mod.id]=mod.group.period
    return schedule

def getTeacherDomains(timetable):
    teachers=Teacher.objects.filter(department=timetable.tableYear.department).order_by('name')
    teacher_dict={}
    for teacher in teachers:
        av=Availability.objects.filter(teacher=teacher)
        availability=[]
        for a in av:
            availability.append(a.period)
        t_dict={'availability':availability, 'load':teacher.load}
        teacher_dict[teacher.id]=t_dict
    return teacher_dict

class CSP():

    def __init__(self, schedule, teachers):
        self.schedule=schedule
        self.teachers=teachers
        self.class_assignments={id:None for id in schedule.keys()}
        
    def isComplete(self):
        return all(teacher is not None for teacher in self.class_assignments.values())

    def isValidAssignment(self, teacherId, classId):
        classPeriod=self.schedule[classId]
        if classPeriod not in self.teachers[teacherId]['availability']:
            return False
        checkLoad= [cl for cl, teacher in self.class_assignments.items() if teacher==teacherId]
        if len(checkLoad)>=self.teachers[teacherId]['load']:
            return False
        for cl in checkLoad:
            if self.schedule[cl] == classPeriod:
                return False
        return True

    def assignTeacher(self):
        if self.isComplete():
            return True
        
        unassigned=[]
        for cl, t in self.class_assignments.items():
            if t is None:
                unassigned.append(cl)
        classId=unassigned[0]
        for teacher in self.teachers.keys():
            if self.isValidAssignment(teacher, classId):
                self.class_assignments[classId]=teacher
                if self.assignTeacher():
                    return True
                self.class_assignments[classId]=None
        return False



