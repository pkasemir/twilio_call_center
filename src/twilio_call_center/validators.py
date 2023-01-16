import phonenumbers

from django.conf import settings
from django.core.exceptions import ValidationError

def validate_phone_number(value):
    phone_error = ValidationError("Phone number must be valid phone number")
    default_country = getattr(settings,
                              'TWILIO_CALL_CENTER_DEFAULT_COUNTRY', 'US')
    try:
        phone_input = phonenumbers.parse(value, default_country)
        if not phonenumbers.is_valid_number(phone_input):
            raise phone_error
    except:
        raise phone_error
