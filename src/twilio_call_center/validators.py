import phonenumbers

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator

from .utils import split_list_or_empty, parse_phone_number


def validate_phone_number(value):
    phone_error = ValidationError("Enter a valid phone number.")
    try:
        phone_input = parse_phone_number(value)
        if not phonenumbers.is_valid_number(phone_input):
            raise phone_error
    except:
        raise phone_error


def validate_list_using(validator, value):
    for i, item in enumerate(split_list_or_empty(value)):
        try:
            validator(item)
        except ValidationError as e:
            raise ValidationError("{} (at index {})'".format(e.message, i)) from e


def validate_email_list(value):
    validate_list_using(EmailValidator(), value)


def validate_phone_list(value):
    validate_list_using(validate_phone_number, value)


def validate_pin_digits_list(value):
    pin_validator = RegexValidator("^[0-9]{3,10}$",
                                   message='Enter a valid pin, 3-10 digits.')
    validate_list_using(pin_validator, value)
