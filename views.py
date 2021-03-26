from django.http import HttpResponse
from django.urls import reverse

try:
    from django_twilio.client import twilio_client
    from django_twilio.decorators import twilio_view
except Exception as e:
    print(e)
    print("WARNING: Could not start twilio, it's functions will be disabled")

    def twilio_view(fn):
        def twilio_disabled(req):
            resp = 'Cannot open {}. Twilio is disabled'.format(fn.__name__)
            if settings.DEBUG:
                resp += '<br><br>Here is the response<br>'
                resp += '<textarea rows="20" cols="120">{}</textarea>'.format(fn(req))
            return HttpResponse(resp)
        return twilio_disabled

from twilio.twiml.voice_response import VoiceResponse

from .models import MenuItem, twilio_default_transfer


def twilio_say(response, message, voice='woman', **kwargs):
    response.say(message, voice=voice, **kwargs)


def get_query_dict(request):
    if request.method == 'GET':
        return request.GET
    elif request.method == 'POST':
        return request.POST
    return {}


@twilio_view
def call_menu(request):
    response = VoiceResponse()

    # start twilio menu response
    with response.gather(
        num_digits=1, action=reverse("twilio_call_center:call-action"), method="POST",
        timeout=10
    ) as g:
        last_digit = -1
        menu_text = "Thank you for calling White Horse Health and Wellness!"
        entries = MenuItem.objects.filter(enabled=True).order_by('menu_digit')
        for entry in entries:
            # skip empty entries
            if not entry.menu_text and not entry.action_text \
                    and not entry.action_phone:
                continue
            if last_digit >= entry.menu_digit:
                continue

            last_digit = entry.menu_digit

            if entry.menu_text:
                menu_text += " Press {} {}.".format(entry.menu_digit,
                                                    entry.menu_text)

        twilio_say(g, menu_text)
    return response


@twilio_view
def call_action(request):
    response = VoiceResponse()
    last_digit = -1
    action_text = None
    action_phone = None

    query_dict = get_query_dict(request)
    digit = query_dict['Digits']

    entries = MenuItem.objects.filter(enabled=True, menu_digit=digit) \
        .order_by('menu_digit')
    for entry in entries:
        # skip empty entries
        if not entry.menu_text and not entry.action_text \
                and not entry.action_phone:
            continue
        if last_digit >= entry.menu_digit:
            continue

        last_digit = entry.menu_digit

        if digit == str(entry.menu_digit):
            if entry.action_text:
                action_text = entry.action_text
            if entry.action_phone:
                action_phone = entry.action_phone
                if action_text is None:
                    action_text = twilio_default_transfer
            break

    if action_text is not None:
        twilio_say(response, action_text)
    if action_phone is None:
        if action_text is not None:
            response.pause(1)
        response.redirect(reverse("twilio_call_center:call-menu"))
    else:
        response.dial(action_phone)
        response.redirect(reverse("twilio_call_center:call-end"))
    return response


@twilio_view
def call_end(request):
    response = VoiceResponse()
    twilio_say(response, 'Goodbye.')
    response.hangup()
    return response
