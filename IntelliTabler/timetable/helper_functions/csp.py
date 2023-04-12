from ..models import *

def createNewGeneratedTimetable(year, user, name, timetableA):
    t=Timetable.objects.create(name=name, tableYear=year, user=user)
    mgA=ModuleGroup.objects.filter(parent__timetable=timetableA).order_by('name')
    mgB=ModuleGroup.objects.filter(parent__timetable=t).order_by('name')
    for i in range(len(mgB)):
        mgB[i].period=mgA[i].period
        mgB[i].save()
    clonePreferences(timetableA, t)
    return t

def clonePreferences(timetableA, timetableB):
    prefs = Preference.objects.filter(timetable=timetableA)
    for pref in prefs:
        clonedPref=Preference()
        clonedPref.teacher=pref.teacher
        clonedPref.module=Module.objects.get(name=pref.module.name, lesson=pref.module.lesson, lessonNum=pref.module.lessonNum, group__parent__timetable=timetableB)
        clonedPref.priority=pref.priority
        clonedPref.timetable=timetableB
        clonedPref.save()
    

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
        t_dict={'availability':availability, 'load':load, 'dLoad':teacher.load, 'preferences':pdict}
        teacher_dict[teacher.id]=t_dict
        count+=1
    return teacher_dict

class CSP():

    def __init__(self, schedule, teachers, weeks):
        self.schedule=schedule  #Classes and Periods
        self.teachers=teachers  #Teachers and preferences
        self.weeks=weeks #Number of weeks (Helps with checking Load)
        self.unassigned=list(schedule.keys())  #Get variable list
        self.class_assignments={id:None for id in schedule.keys()} #Create assignments dict
        self.preassigned={} #Get dict of any preassigned classes
        self.teacher_splitClass={teacher: {} for teacher in teachers.keys()} #Create Dict to track like classes
        self.assignedPeriods={v['period']:set() for k,v in schedule.items()} #Dict to track which periods a teacher is already in. Helps for quick constraint checking.
        self.currDoms={cl: {} for cl in schedule.keys()}
        toDelete=[]
        for k,v in self.currDoms.items():
            for teacher, val in teachers.items():
                if self.isValidAssignment(teacher, k):
                    if self.schedule[k]['sharedKey'] not in self.teacher_splitClass[teacher]:
                        self.teacher_splitClass[teacher][self.schedule[k]['sharedKey']]=set()
                    if k in val['preferences']:
                        if val['preferences'][k]==3:
                            if k in self.preassigned:
                                raise ValueError("Multiple teachers have been given a required preference for class " + str(k))
                            self.preassigned[k]=teacher
                            self.class_assignments[k]=teacher
                            self.teachers[teacher]['load'][self.schedule[k]['period'].week]-=1
                            self.unassigned.remove(k)
                            self.assignedPeriods[self.schedule[k]['period']].add(teacher)
                            toDelete.append(k)
                            self.teacher_splitClass[teacher][self.schedule[k]['sharedKey']].add(k)
                        else:
                            self.currDoms[k][teacher]={'base_pref':val['preferences'][k], 'sharedKey_pref':0}
                    else:
                        self.currDoms[k][teacher]={'base_pref':0, 'sharedKey_pref':0}

                else:
                    if k in val['preferences']:
                        if val['preferences'][k]==3:
                            raise ValueError("A teacher has been assigned a required class, however that assignment is impossible.")

        tempDom=self.currDoms[k].copy()
        self.currDoms[k].clear()
        self.currDoms[k] = {teacher: vals for teacher, vals in sorted(tempDom.items(), key=lambda t: (t[1]['base_pref'], t[1]['sharedKey_pref']), reverse=True)}
        for k in toDelete:
            del self.currDoms[k]

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
        

        self.unassigned.sort(key=lambda cl: (len(self.currDoms[cl]), -self.currDoms[cl][next(iter(self.currDoms[cl]))]['base_pref'] if self.currDoms[cl] else 0))
        classId=self.unassigned[0]
        domain=self.currDoms[classId]
        if not domain:
            return False

        
        #Get list of teachers by highest remaining load
        for teacher in sorted(domain, key=lambda t: (domain[t]['base_pref'], domain[t]['sharedKey_pref'], self.teachers[t]['load'][self.schedule[classId]['period'].week]/self.teachers[t]['dLoad']), reverse=True):
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
                self.teacher_splitClass[teacher][self.schedule[classId]['sharedKey']].add(classId)
                self.forwardCheck(classId, teacher)

                #Run recursive step
                if self.assignTeacher():
                    return True
                
                #Else set assignment to none, add back the load, add back the class, and remove teacher from period
                self.class_assignments[classId]=None
                self.teachers[teacher]['load'][self.schedule[classId]['period'].week]+=1
                self.unassigned.append(classId)
                self.assignedPeriods[self.schedule[classId]['period']].remove(teacher)
                self.teacher_splitClass[teacher][self.schedule[classId]['sharedKey']].remove(classId)
                self.currDoms[classId]=domain
            else:
                del domain[teacher]
                

        return False


    def forwardCheck(self, classId, teacherId):
        sKey = self.schedule[classId]['sharedKey']
        for nextCl in self.unassigned:
            changed=False
            if nextCl == classId:
                continue
            if teacherId in self.currDoms[nextCl]:
                if not self.isValidAssignment(teacherId, nextCl):
                    del self.currDoms[nextCl][teacherId]
                else:
                    self.currDoms[nextCl][teacherId]['sharedKey_pref'] = len({sk for sk in self.teacher_splitClass[teacherId][self.schedule[nextCl]['sharedKey']]})
                    changed=True
            else:
                if self.isValidAssignment(teacherId, nextCl):
                    if nextCl in self.teachers[teacherId]['preferences']:
                        base=self.teachers[teacherId]['preferences'][nextCl]
                    else: base=0
                    self.currDoms[nextCl][teacherId] = {'base_pref': base, 'sharedKey_pref': len({sk for sk in self.teacher_splitClass[teacherId][self.schedule[nextCl]['sharedKey']]})}
                    changed=True
            if changed:
                tempDom=self.currDoms[nextCl].copy()
                self.currDoms[nextCl].clear()
                self.currDoms[nextCl] = {teacher: vals for teacher, vals in sorted(tempDom.items(), key=lambda t: (t[1]['base_pref'], t[1]['sharedKey_pref']), reverse=True)}
                

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
                availableLoad[i]+=dict['dLoad']
       
        for week in range(1,self.weeks+1):
            if loadCheck[week]>availableLoad[week]:
                return False
        return True
