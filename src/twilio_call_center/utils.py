import phonenumbers

from django.conf import settings

try:
    from django_twilio.client import twilio_client
    from django_twilio.decorators import twilio_view
except Exception as e:
    print(e)
    print("WARNING: Could not start twilio, it's functions will be disabled")

    twilio_client = None

    def twilio_view(fn):
        def twilio_disabled(req):
            resp = 'Cannot open {}. Twilio is disabled'.format(fn.__name__)
            if settings.DEBUG:
                resp += '<br><br>Here is the response<br>'
                resp += '<textarea rows="20" cols="120">{}</textarea>'.format(fn(req))
            return HttpResponse(resp)
        return twilio_disabled


def split_csv_list(csv_list):
    return list(map(str.strip, csv_list.split(',')))


def split_list_or_empty(csv_list):
    # CharFields should properly give None when null=True, but TextFields
    # will give '' string, so we catch both cases here
    if csv_list is None or len(csv_list) == 0:
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
