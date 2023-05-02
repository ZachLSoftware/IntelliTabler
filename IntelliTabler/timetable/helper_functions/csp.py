from ..models import *

"""
Creates a table copy for auto assignment
"""
def createNewGeneratedTimetable(year, name, timetableA):
    t=Timetable.objects.create(name=name, tableYear=year, generating=True)
    mgA=ModuleGroup.objects.filter(parent__timetable=timetableA).order_by('name')
    mgB=ModuleGroup.objects.filter(parent__timetable=t).order_by('name')
    #Copies period assignments
    for i in range(len(mgB)):
        mgB[i].period=mgA[i].period
        mgB[i].save()
    clonePreferences(timetableA, t)
    return t

"""
Clones teacher preferences to a new timetable
"""
def clonePreferences(timetableA, timetableB):
    prefs = Preference.objects.filter(timetable=timetableA)
    for pref in prefs:
        clonedPref=Preference()
        clonedPref.teacher=pref.teacher
        clonedPref.module=Module.objects.get(name=pref.module.name, lesson=pref.module.lesson, lessonNum=pref.module.lessonNum, group__parent__timetable=timetableB)
        clonedPref.priority=pref.priority
        clonedPref.timetable=timetableB
        clonedPref.save()
    
"""
Gets and packages modules ready for CSP
"""
def getClassSchedule(timetable):
    modules=Module.objects.filter(group__parent__timetable=timetable).order_by('group', 'name')
    schedule={}
    for mod in modules:
        if mod.group.period==None:
            return False
        schedule[mod.id]={'sharedKey':mod.sharedKey,'period':mod.group.period, 'repeat':mod.group.parent.repeat}
    return schedule

"""
Gets and packages teachers ready for CSP
"""
def getTeacherDomains(timetable):
    teachers=Teacher.objects.filter(department=timetable.tableYear.department).order_by('name')
    teacher_dict={}
    w=timetable.tableYear.department.format.numWeeks
    count=0
    for teacher in teachers:
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
    def __init__(self, schedule, teachers, weeks, verify=False):
        self.schedule=schedule  #Classes and Periods
        self.teachers=teachers  #Teachers and preferences
        self.weeks=weeks #Number of weeks (Helps with checking Load)
        self.unassigned=list(schedule.keys())  #Get variable list
        self.class_assignments={id:None for id in schedule.keys()} #Create assignments dict
        self.preassigned={} #Get dict of any preassigned classes
        self.teacher_splitClass={teacher: {} for teacher in teachers.keys()} #Create Dict to track like classes
        self.assignedPeriods={v['period']:set() for k,v in schedule.items()} #Dict to track which periods a teacher is already in. Helps for quick constraint checking.
        self.currDoms={cl: {} for cl in schedule.keys()}
        self.repeatConstraint=True
        if not verify:
            self.setCurrDom() #Create the Current Domains and prune
        
    #Clears current assignments
    def resetAssignments(self):
        self.class_assignments={id:None for id in self.schedule.keys()}

    #Sets up the domains for each class
    def setCurrDom(self):
        toDelete=[] #List to remove domains. Prevents messing up the loop.

        #Loop through all currDoms, then teachers
        for k,v in self.currDoms.items():
            for teacher, val in self.teachers.items():
                if self.isValidAssignment(teacher, k): #Check if teacher/class assignment is valid

                    #Create sharedKey pref set if does not exist
                    if self.schedule[k]['sharedKey'] not in self.teacher_splitClass[teacher]:
                        self.teacher_splitClass[teacher][self.schedule[k]['sharedKey']]=set()

                    #Does the teacher have a preference for the class?
                    if k in val['preferences']:
                        if val['preferences'][k]==3: #If required, assign

                            #If already pre-assigned return error
                            if k in self.preassigned:
                                try:
                                    modName=Module.objects.get(id=k).name
                                except:
                                    modName="Unknown"
                                raise ValueError("Multiple teachers have been given a required preference for class " + modName)
                            
                            #Assign teacher
                            self.preassigned[k]=teacher
                            self.class_assignments[k]=teacher
                            self.teachers[teacher]['load'][self.schedule[k]['period'].week]-=1 #Upate teacher load
                            self.unassigned.remove(k) #Remove class from unassigned
                            self.assignedPeriods[self.schedule[k]['period']].add(teacher) #Add period to assigned periods for the teacher
                            toDelete.append(k) #Add to delete list for removing from currdom
                            self.teacher_splitClass[teacher][self.schedule[k]['sharedKey']].add(k) #Add class to splitclass list for the teacher
                        else:
                            self.currDoms[k][teacher]={'base_pref':val['preferences'][k], 'sharedKey_pref':0} #Set preference if not 3
                    else:
                        self.currDoms[k][teacher]={'base_pref':0, 'sharedKey_pref':0} #Set to 0 if no preference

                #If class is invalid and is set to required, return error.
                else:
                    if k in val['preferences']:
                        if val['preferences'][k]==3:
                            raise ValueError("A teacher has been assigned a required class, however that assignment is impossible.")

        #Sort domains and clean up currDoms
        tempDom=self.currDoms[k].copy()
        self.currDoms[k].clear()
        self.currDoms[k] = {teacher: vals for teacher, vals in sorted(tempDom.items(), key=lambda t: (t[1]['base_pref'], t[1]['sharedKey_pref']), reverse=True)}
        for k in toDelete:
            del self.currDoms[k]

    #Check if all classes have assignments
    def isComplete(self):
        return all(teacher is not None for teacher in self.class_assignments.values())

    #Constraint Function
    def isValidAssignment(self, teacherId, classId):
        classPeriod=self.schedule[classId]['period']
        cl = self.schedule[classId]
        if classPeriod not in self.teachers[teacherId]['availability']: #Check if teacher is available
            return False
        if teacherId in self.assignedPeriods[classPeriod]: #Check if teacher is already teaching in that period
            return False
        if self.teachers[teacherId]['load'][self.schedule[classId]['period'].week]<=0: #Check if teacher has any load left.
            return False
        if self.schedule[classId]['repeat'] and self.repeatConstraint: #Check if split between weeks.
            classes=[c for c,val in self.schedule.items() if (val['sharedKey']==cl['sharedKey'] and val['period'].name == cl['period'].name and c != classId)]
            for clas in classes:
                if self.class_assignments[clas] and teacherId != self.class_assignments[clas]:
                    return False
        return True

    #Backtracking Algorithm
    def assignTeacher(self):
        #Check if done
        if self.isComplete():
            return True
        
        #Sort unassigned list based on each domain. First by domain length, then preference, then by number of like classes taught.
        self.unassigned.sort(key=lambda cl: (len(self.currDoms[cl]), (-self.currDoms[cl][next(iter(self.currDoms[cl]))]['base_pref'],-self.currDoms[cl][next(iter(self.currDoms[cl]))]['sharedKey_pref']) if self.currDoms[cl] else (0,0)))
        classId=self.unassigned[0] #Select first class
        domain=self.currDoms[classId] #Grab domain for class

        #If domain is empty, backtrack
        if not domain:
            return False
        
        #Copy current domain incase
        domainSave=domain.copy()
        
        #Get list of teachers by highest remaining load
        for teacher in sorted(domain, key=lambda t: (domain[t]['base_pref'], domain[t]['sharedKey_pref'], self.teachers[t]['load'][self.schedule[classId]['period'].week]/self.teachers[t]['dLoad']), reverse=True):
            if self.isValidAssignment(teacher, classId):
                
                #If valid assignment, assign teacher, reduce load for that week,
                #Remove class from unassigned, add teacher to period

                self.class_assignments[classId]=teacher
                self.teachers[teacher]['load'][self.schedule[classId]['period'].week]-=1
                self.unassigned.remove(classId)
                self.assignedPeriods[self.schedule[classId]['period']].add(teacher)
                del self.currDoms[classId]
                self.teacher_splitClass[teacher][self.schedule[classId]['sharedKey']].add(classId)
                self.forwardCheck(teacher)

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

    #Forward Checking algorithm
    def forwardCheck(self, teacherId):
        for nextCl in self.unassigned:
            changed=False #Set changed flag

            #If teacher is already in current domain
            if teacherId in self.currDoms[nextCl]:
                #If teacher is not valid anymore, remove, else update preference scores
                if not self.isValidAssignment(teacherId, nextCl):
                    del self.currDoms[nextCl][teacherId]    
                else:
                    self.currDoms[nextCl][teacherId]['sharedKey_pref'] = len({sk for sk in self.teacher_splitClass[teacherId][self.schedule[nextCl]['sharedKey']]})
                    changed=True
            
            #If teacher isn't in domain, check if they are now valid
            else:
                if self.isValidAssignment(teacherId, nextCl):

                    #Add teacher to domain, adding preferences
                    if nextCl in self.teachers[teacherId]['preferences']:
                        base=self.teachers[teacherId]['preferences'][nextCl]
                    else: base=0
                    self.currDoms[nextCl][teacherId] = {'base_pref': base, 'sharedKey_pref': len({sk for sk in self.teacher_splitClass[teacherId][self.schedule[nextCl]['sharedKey']]})}
                    changed=True
            
            #Sort the domain based on preference and like classes
            if changed:
                tempDom=self.currDoms[nextCl].copy()
                self.currDoms[nextCl].clear()
                self.currDoms[nextCl] = {teacher: vals for teacher, vals in sorted(tempDom.items(), key=lambda t: (t[1]['base_pref'], t[1]['sharedKey_pref']), reverse=True)}

    #Check if there aren't enough teachers or load.
    def checkPossible(self):

        #Check total load per week with classes per week
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
                raise ValueError("There are too many classes ("+str(loadCheck[week])+") and not enough teachers to cover ("+ str(availableLoad[week])+").")
            
        #Check if too many classes have been assigned to a period for the number of teachers.
        periodCount={}
        for module in self.schedule.values():
            p=module['period']
            if p not in periodCount:
                periodCount[p]=1
            else:
                periodCount[p]+=1
        for period,pc in periodCount.items():
            if pc > len(self.teachers):
                raise ValueError("Too many classes have been assigned for the period " + period.name + " and there are not enough teachers to cover it.")

        return True #Return true if checks pass
    
    #Verify current assignments
    def verifyAssignments(self, assignments):
        for cl in assignments:
            if not self.isValidAssignment(cl.teacher.id, cl.id):
                return False
            self.teachers[cl.teacher.id]['load'][self.schedule[cl.id]['period'].week]-=1
            self.assignedPeriods[self.schedule[cl.id]['period']].add(cl.teacher.id)
            
        return True
