import phonenumbers

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator

from .utils import split_csv_list


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


def validate_email_list(value):
    if value is None:
        return
    for i, email in enumerate(split_csv_list(value)):
        validate = EmailValidator(
                message='Enter a valid email (for index ' + str(i) + ')')
        validate(email)


def validate_pin_digits_list(value):
    if value is None:
        return
    for i, digits in enumerate(split_csv_list(value)):
        validate = RegexValidator("^[0-9]{3,10}$",
                message='Enter a valid pin, 3-10 digits (for index ' +
                        str(i) + ')')
        validate(digits)
