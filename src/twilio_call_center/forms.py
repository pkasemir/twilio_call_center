from django import forms
from django.core.validators import validate_email, MaxLengthValidator

from .validators import validate_name, validate_phone_number

class SMSCenterForm(forms.Form):
    message = forms.CharField(required=True, max_length=1600,
                              validators=[MaxLengthValidator(1600)],
                              widget=forms.Textarea(attrs={'rows':5}))
    phone = forms.CharField(required=True, validators=[validate_phone_number])
