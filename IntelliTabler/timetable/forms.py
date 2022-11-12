from django import forms
from .models import *

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ("name",)


class FormatForm(forms.ModelForm):
    class Meta:
        model=Format
        fields = ("numPeriods","numWeeks",)
