from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm
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
        exclude={"user","department", "id"}

class AvailabilityForm(BaseForm):
    checked = forms.BooleanField(required=False)
    period = forms.CharField()
    week = forms.IntegerField()

class ModuleParentForm(BaseModelForm):
    name = forms.CharField(label="Class Name")
    numPeriods=forms.IntegerField(label="Number of periods for class", validators=[validate_positive])
    numClasses=forms.IntegerField(label="Number of class groups", validators=[validate_positive])
    class Meta:
        model=ModuleParent
        exclude=("year","department", "user", "id")
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

    def clean(self):
        if not self.edit:
            cleaned_data=super().clean()
            name=cleaned_data['name']
            year=Year.objects.filter(id=self.year)[0]
            if(ModuleParent.objects.filter(name=name, year=self.year, department=self.department).exists()):
                self.add_error('name', _('Module: {} already exists for year: {}').format(name, year.year))

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
            self.add_error("year","You cannot have multiple timetables for the same department in the same year.")
        
        
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
    group=forms.ChoiceField(widget=forms.Select(attrs={'id': 'groupChoice'}))
    module=forms.ChoiceField(widget=forms.Select(attrs={'id': 'moduleChoice'}))
    assignToAll=forms.BooleanField(required=False, label="Assign to all instances of class?",widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def __init__(self, groups, modules, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if(groups==[]):
            self.fields['group'].choices=[('None', 'None'),]
            self.fields['group'].widget.attrs['disabled']=True
            self.fields['module'].widget.attrs['disabled']=True
        else:
            self.fields['group'].choices = groups
            self.fields['module'].choices= modules

class changeColorForm(BaseForm):
    color = forms.CharField(max_length=7, help_text="The color you would like the module to appear in calendars and charts.", widget=forms.TextInput(attrs={'type': 'color', 'class':'form-control-color'}))