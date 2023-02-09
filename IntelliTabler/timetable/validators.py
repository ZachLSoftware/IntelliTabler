from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_positive(value):
    if value < 0:
        raise ValidationError(
            _('This value cannot be negative, please enter a positive number.'),
        )
    elif value==0:
        raise ValidationError(
            _('This value cannot be 0, please enter a positive number.'),
        )