import phonenumbers

from django.conf import settings


def split_csv_list(csv_list):
    return list(map(str.strip, csv_list.split(',')))


def split_list_or_empty(csv_list):
    if len(csv_list) == 0:
        return []
    else:
        return split_csv_list(csv_list)


def parse_phone_number(number):
    ''' Parse the string argument into a PhoneNumber.

    May raise a NumberParseException per phonenumbers.parse() function.'''
    default_country = getattr(settings,
                              'TWILIO_CALL_CENTER_DEFAULT_COUNTRY', 'US')
    return phonenumbers.parse(number, default_country)


def phone_numbers_equal(n1, n2):
    ''' Checks if two strings representing phone numbers are the same.'''
    if n1 == n2:
        return True
    try:
        phone1 = parse_phone_number(n1)
        phone2 = parse_phone_number(n2)
        return phone1 == phone2
    except:
        # one of the numbers failed to parse
        return False
