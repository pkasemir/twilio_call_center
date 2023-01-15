import phonenumbers

from django.core.exceptions import ValidationError

def validate_phone_number(value):
    try:
        phone_input = phonenumbers.parse(value, 'US')
        if not phonenumbers.is_valid_number(phone_input):
            raise ValidationError("Phone number must be valid US phone number")
    except:
        raise ValidationError("Phone number must be valid US phone number")
