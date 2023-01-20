from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

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

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ("name",)


class FormatForm(forms.ModelForm):
    class Meta:
        model=Format
        fields = ("numPeriods","numWeeks",)


class TeacherForm(forms.ModelForm):
    class Meta:
        model=Teacher
        fields = ("name", "totalHours", "roomNum", "id")
        widgets = {
            "id": forms.HiddenInput(),
        }

class AvailabilityForm(forms.Form):
    checked = forms.BooleanField(required=False)
    period = forms.CharField()
    week = forms.IntegerField()

class ModuleGroupForm(forms.ModelForm):
    class Meta:
        model=ModuleGroup
        fields=("name","numPeriods", "numClasses")

    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop('year', None)
        self.department = kwargs.pop('department', None)
        self.edit = kwargs.pop('edit', False)
        super(ModuleGroupForm, self).__init__(*args, **kwargs)

    def clean(self):
        if not self.edit:
            cleaned_data=super().clean()
            name=cleaned_data['name']
            year=Year.objects.filter(id=self.year)[0]
            if(ModuleGroup.objects.filter(name=name, year=self.year, department=self.department).exists()):
                raise ValidationError(
                    _('Module: %(value)s already exists for year: %(year)s'),
                    params={'value': name, 'year': year.year})

class YearForm(forms.ModelForm):
    class Meta:
        model=Year
        fields=("year",)

class AssignTeacherForm(forms.Form):
    teacher=forms.ChoiceField()
    
    def __init__(self, teachers, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].choices = teachers

class AssignPeriodForm(forms.Form):
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
