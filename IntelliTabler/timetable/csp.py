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
        if mod.group.period==None:
            return False
        schedule[mod.id]={'sharedKey':mod.sharedKey,'period':mod.group.period}
    return schedule

def getTeacherDomains(timetable):
    teachers=Teacher.objects.filter(department=timetable.tableYear.department).order_by('name')
    teacher_dict={}
    w=timetable.tableYear.department.format.numWeeks
    count=0
    for teacher in teachers:
        # if count == 6:
        #     break
        av=Availability.objects.filter(teacher=teacher)
        pr=Preference.objects.filter(teacher=teacher)
        pdict={}
        for p in pr:
            pdict[p.module.id]=p.priority
        availability=set()
        for a in av:
            availability.add(a.period)
        load={}
        for w in range(1,w+1):
            load[w]=teacher.load
        t_dict={'availability':availability, 'load':load, 'dLoad':teacher.load, 'prefrences':pdict}
        teacher_dict[teacher.id]=t_dict
        count+=1
    return teacher_dict

class CSP():

    def __init__(self, schedule, teachers, weeks):
        self.schedule=schedule
        self.teachers=teachers
        self.class_assignments={id:None for id in schedule.keys()}
        self.weeks=weeks
        self.unassigned=list(schedule.keys())
        self.assignedPeriods={}
        for k,v in schedule.items():
            self.assignedPeriods[v['period']]=set()
        self.currDoms={cl: {} for cl in schedule.keys()}
        for k,v in self.currDoms.items():
            for teacher, val in teachers.items():
                if k in val['prefrences']:
                    self.currDoms[k][teacher]=val['prefrences'][k]
                else:
                    self.currDoms[k][teacher]=0
        
    def isComplete(self):
        return all(teacher is not None for teacher in self.class_assignments.values())

    def isValidAssignment(self, teacherId, classId):
        classPeriod=self.schedule[classId]['period']
        if classPeriod not in self.teachers[teacherId]['availability']:
            return False
        if teacherId in self.assignedPeriods[classPeriod]:
            return False
        if self.teachers[teacherId]['load'][self.schedule[classId]['period'].week]<=0:
            return False
        return True


    def assignTeacher(self):
        if self.isComplete():
            return True
        
        classId=self.unassigned[0]
        domain=self.currDoms[classId]
        if not domain:
            return False

        
        #Get list of teachers by highest remaining load
        teachers = sorted(domain, key=lambda t: (domain[t], self.teachers[t]['load'][self.schedule[classId]['period'].week]/self.teachers[t]['dLoad']), reverse=True)
        print('\n****START****\n', teachers, '\n*****END*****\n')
        for teacher in teachers:
            if teacher not in domain.keys():
                continue
            if self.isValidAssignment(teacher, classId):
                
                #If valid assignment, assign teacher, reduce load for that week,
                #Remove class from unassigned, add teacher to period

                self.class_assignments[classId]=teacher
                self.teachers[teacher]['load'][self.schedule[classId]['period'].week]-=1
                self.unassigned.remove(classId)
                self.assignedPeriods[self.schedule[classId]['period']].add(teacher)
                del self.currDoms[classId]
                self.forwardCheck(classId, teacher)

                #Run recursive step
                if self.assignTeacher():
                    return True
                
                #Else set assignment to none, add back the load, add back the class, and remove teacher from period
                self.class_assignments[classId]=None
                self.teachers[teacher]['load'][self.schedule[classId]['period'].week]+=1
                self.unassigned.append(classId)
                self.assignedPeriods[self.schedule[classId]['period']].remove(teacher)
                self.currDoms[classId]=domain
            else:
                del domain[teacher]
                

        return False


    def forwardCheck(self, classId, teacherId):
        sKey=self.schedule[classId]['sharedKey']
        for nextCl in self.unassigned:
            if nextCl==classId:
                continue
            if teacherId in self.currDoms[nextCl]:
                if not self.isValidAssignment(teacherId, nextCl):
                   del self.currDoms[nextCl][teacherId]
                else:
                    if self.schedule[nextCl]['sharedKey']==sKey:
                        self.currDoms[nextCl][teacherId]+=1

    def checkPossible(self):
        loadCheck={}
        availableLoad={}
        for i in range(1, self.weeks+1):
            loadCheck[i]=0
            availableLoad[i]=0
        for cl, v in self.schedule.items():
            loadCheck[v['period'].week]+=1
        
        for teacher, dict in self.teachers.items():
            for i in range(1,self.weeks+1):
                availableLoad[i]+=dict['load'][i]
       
        for week in range(1,self.weeks+1):
            if loadCheck[week]>availableLoad[week]:
                return False
        return True

    # def forwardCheck(self, assignments, unassigned):
    #     pruned={}
    #     partAssign=assignments.copy()
    #     for cl in unassigned:
    #         pruned[cl]=set()
    #         for teacher in self.teachers.keys():
    #             if self.isValidAssignment(teacher,cl):
    #                 partAssign[cl]=teacher
    #                 valid=True

    #                 for nextCl in unassigned:
    #                     if nextCl==cl:
    #                         continue
    #                     dom = [t for t in self.teachers.keys() if self.isValidAssignment(t, nextCl)]

    #                     if not dom:
    #                         valid=False
    #                         break
    #                 if valid:
    #                     pruned[cl].add(teacher)
    #                 partAssign[cl]=None
    #             else:
    #                 partAssign[cl]=None
    #     return pruned

