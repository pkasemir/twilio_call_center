from django import forms
from django.core.validators import MaxLengthValidator

from .models import TwilioNumber, TelInput
from .validators import validate_phone_number

class SendSmsForm(forms.Form):
    from_phone = forms.ModelChoiceField(queryset=TwilioNumber.objects.all())
    to_phone = forms.CharField(required=True,
                               validators=[validate_phone_number],
                               widget=TelInput())
    message = forms.CharField(required=True, max_length=1600,
                              validators=[MaxLengthValidator(1600)],
                              widget=forms.Textarea(attrs={'rows':5}))
