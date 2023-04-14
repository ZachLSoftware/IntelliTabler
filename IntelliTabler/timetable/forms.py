from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm, PasswordResetForm
from django.forms.widgets import TextInput
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .validators import *

class BaseForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')  
        super(BaseForm, self).__init__(*args, **kwargs)

class BaseModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(BaseModelForm, self).__init__(*args, **kwargs)

class RegistrationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("username", "email", )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = """
            <ul>
                <li id="charLength">Your password must contain at least 8 characters.</li>
                <li id="numCheck">Your password can’t be entirely numeric.</li>
            </ul>"""
    
    def clean(self):
        cleaned_data=super().clean()
        email = cleaned_data['email']
        if User.objects.filter(email=email).exists():
            self.add_error('email', 'A user with that email already exists.')

class changePassword(SetPasswordForm):
    class Meta:
        model = get_user_model()
        fields = ['new_password1', 'new_password2']


class passwordResetForm(BaseForm):
    email = forms.EmailField()

class DepartmentForm(BaseForm):
    name = forms.CharField(max_length=30, label="Department Name")
    numPeriods=forms.IntegerField(label=_("Number of Periods Per Day"), validators=[validate_positive], help_text="The number of periods that happen each day.")
    numWeeks=forms.IntegerField(label=_("Number of recurring weeks"), validators=[validate_positive], help_text="The number of weeks before the schedule repeats.")



class TeacherForm(BaseModelForm):
    name = forms.CharField(label="Teacher Name")
    load = forms.IntegerField(label="Contracted Hours", validators=[validate_positive])
    roomNum = forms.CharField(max_length=20, label="Room")
    class Meta:
        model=Teacher
        exclude={"department", "id"}

class AvailabilityForm(BaseForm):
    checked = forms.BooleanField(required=False)
    period = forms.CharField()
    week = forms.IntegerField()

class ModuleParentForm(BaseModelForm):
    name = forms.CharField(label="Class Name")
    numPeriods=forms.IntegerField(label="Number of periods for class", validators=[validate_positive])
    numClasses=forms.IntegerField(label="Number of class groups", validators=[validate_positive])
    repeat=forms.BooleanField(required=False, label="Does this class repeat the same schedule each week?", widget=forms.CheckboxInput(attrs={'type': 'checkbox', 'class': 'form-check-input'}))
    class Meta:
        model=ModuleParent
        exclude=("timetable","department", "id", "sharedId")
        widgets={
            'color': TextInput(attrs={'type': 'color', 'class':'form-control-color'}),
        }
        help_texts={
            'color':"The color you would like the module to appear in calendars and charts.", 
        }

    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop('year', None)
        self.department = kwargs.pop('department', None)
        self.edit = kwargs.pop('edit', False)
        super(ModuleParentForm, self).__init__(*args, **kwargs)

    def clean_repeat(self):
        repeat = self.cleaned_data.get('repeat')
        if repeat:
            if self.cleaned_data['numPeriods']%self.department.format.numWeeks!=0:
                self.add_error('repeat', _('The number of periods must evenly divide into the number of weeks ({}) for repeat to work properly.').format(self.department.format.numWeeks))
        return repeat

    def clean(self):
        #if not self.edit:
        cleaned_data=super().clean()
        name=cleaned_data['name']
        year=Year.objects.filter(id=self.year)[0]
        if(ModuleParent.objects.filter(name=name, timetable=year.defaultTimetable, department=self.department).exclude(id=self.instance.id).exists()):
            self.add_error('name', _('Module: {} already exists for Year: {}').format(name, year.year))

class YearForm(BaseModelForm):
    department = forms.ChoiceField()
    class Meta:
        model=Year
        fields=("year",)

    def __init__(self, departments, *args, **kwargs):
        super(YearForm, self).__init__(*args, **kwargs)
        self.fields['department'].choices=departments

    def clean(self):
        cleaned_data=super(YearForm, self).clean()
        year = cleaned_data["year"]
        if(Year.objects.filter(department_id=cleaned_data["department"], year=year).exists()):
            self.add_error("year","Select a new year for the department.")

        return cleaned_data
    

class AssignTeacherForm(BaseForm):
    teacher=forms.ChoiceField()
    assignToAll=forms.BooleanField(required=False, label="Assign to all instances of class?",widget=forms.CheckboxInput(attrs={'type': 'checkbox', 'class': 'form-check-input'}))
    
    def __init__(self, teachers, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].choices = teachers

class AssignPeriodForm(BaseForm):
    template_name="forms/period_form_snippet.html"
    DAYS=(
        ("Mon", "Mon"),
        ("Tues", "Tues"),
        ("Wed", "Wed"),
        ("Thurs", "Thurs"),
        ("Fri", "Fri")
    )
    week=forms.ChoiceField()
    day=forms.ChoiceField(choices=DAYS)
    period=forms.ChoiceField()
    
    def __init__(self, weeks, periods, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['week'].choices = weeks
        self.fields['period'].choices = periods

class addEventForm(BaseForm):
    group=forms.ChoiceField()


    def __init__(self, groups, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if(groups==[]):
            self.fields['group'].choices=[('None', 'None'),]
            self.fields['group'].widget.attrs['disabled']=True
        else:
            self.fields['group'].choices = groups


class addTeacherCombingForm(BaseForm):
    moduleParent=forms.ChoiceField(label="class", choices=[('None','None')], widget=forms.Select(attrs={'id': 'parentChoice'}))
    group=forms.ChoiceField(choices=[('Select Class','Select Class')], widget=forms.Select(attrs={'id': 'groupChoice'}))
    module=forms.ChoiceField(choices=[('Select Group','Select Group')], widget=forms.Select(attrs={'id': 'moduleChoice'}))
    assignToAll=forms.BooleanField(required=False, label="Assign to all instances of class?",widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def __init__(self, parents,groups=[],modules=[],*args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if(parents==[]):
            self.fields['moduleParent'].choices=[('None', 'None Unassigned'),]
            self.fields['moduleParent'].widget.attrs['disabled']=True
            self.fields['group'].widget.attrs['disabled']=True
            self.fields['module'].widget.attrs['disabled']=True
            self.fields['assignToAll'].widget.attrs['disabled']=True
        elif(groups==[] or modules==[]):
            self.fields['moduleParent'].choices = parents
            self.fields['group'].choices=[('Select Group','Select Group')]
            self.fields['module'].choices=[('Select Group','Select Group')]
            self.fields['group'].widget.attrs['disabled']=True
            self.fields['module'].widget.attrs['disabled']=True
        else:
            self.fields['moduleParent'].choices = parents
            self.fields['group'].choices = groups
            self.fields['module'].choices = modules

class changeColorForm(BaseForm):
    color = forms.CharField(max_length=7, help_text="The color you would like the module to appear in calendars and charts.", widget=forms.TextInput(attrs={'type': 'color', 'class':'form-control-color'}))

class TimetableForm(BaseModelForm):
    name=forms.CharField(max_length=20)
    default=forms.BooleanField(required=False, label="Set as default timetable?",widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model=Timetable
        exclude=("id","tableYear")


class setPreferenceForm(BaseForm):
    choices=[(3,"REQUIRED"),(2,"HIGH"),(1,"MEDIUM"),(0,"NONE")]
    moduleParent=forms.ChoiceField(label="class", choices=[('None','None')], widget=forms.Select(attrs={'id': 'parentChoice'}))
    group=forms.ChoiceField(choices=[('Select Class','Select Class')], widget=forms.Select(attrs={'id': 'groupChoice'}))
    module=forms.ChoiceField(choices=[('Select Group','Select Group')], widget=forms.Select(attrs={'id': 'moduleChoice'}))
    priority=forms.ChoiceField(choices=choices)
    assignToAll=forms.BooleanField(required=False, label="Assign to all instances of class?",widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def __init__(self, parents,groups=[],modules=[],*args, **kwargs):
        self.teacherId = kwargs.pop('teacherId', None)
        super().__init__(*args, **kwargs)
        if(parents==[]):
            self.fields['class'].choices=[('None', 'None'),]
        elif(groups==[] or modules==[]):
            self.fields['moduleParent'].choices = parents
            self.fields['group'].choices=[('Select Group','Select Group')]
            self.fields['module'].choices=[('Select Group','Select Group')]
            self.fields['group'].widget.attrs['disabled']=True
            self.fields['module'].widget.attrs['disabled']=True
        else:
            self.fields['moduleParent'].choices = parents
            self.fields['group'].choices = groups
            self.fields['module'].choices = modules
            self.fields['group'].widget.attrs['disabled']=True
            self.fields['module'].widget.attrs['disabled']=True

    def clean(self):
        cleaned_data=super().clean()
        if Preference.objects.filter(teacher_id=self.teacherId, module_id=cleaned_data['module']).exists():
            self.add_error("module","This teacher already has a preference set for this module.")


class UploadFileForm(BaseForm):
    file=forms.FileField()

class TemplateChoices(BaseForm):
    Teachers=forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'id':'teacherTemplateCheck', 'type': 'checkbox', 'class': 'form-check-input templateSelectorForm'}))
    Classes=forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'id':'classTemplateCheck', 'type': 'checkbox', 'class': 'form-check-input templateSelectorForm'}))
    Schedule=forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'id':'scheduleTemplateCheck', 'type': 'checkbox', 'class': 'form-check-input templateSelectorForm templatesNoClass'}))
    Preferences=forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'id':'preferenceTemplateCheck', 'type': 'checkbox', 'class': 'form-check-input templateSelectorForm templatesNeither'}))
    Assignments=forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'id':'assignTemplateCheck', 'type': 'checkbox', 'class': 'form-check-input templateSelectorForm templatesNeither'}))