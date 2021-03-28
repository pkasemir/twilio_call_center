from django.http import Http404, HttpResponse
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

from .models import Menu, MenuItem, twilio_default_transfer, \
    twilio_default_voice


def twilio_say(menu, response, message, **kwargs):
    if menu.voice is None:
        voice = twilio_default_voice
    else:
        voice = menu.voice.voice
    response.say(message, voice=voice, **kwargs)


def get_query_dict(request):
    if request.method == 'GET':
        return request.GET
    elif request.method == 'POST':
        return request.POST
    return {}


def call_reverse(name, page):
    return reverse("twilio_call_center:" + page, kwargs={"name":name})


def get_menu(name):
    menu = Menu.objects.filter(enabled=True, name=name)
    if len(menu) == 0:
        raise Http404("Call Center menu {} doesn't exist.".format(name))

    return menu.first()


def get_menu_items(menu):
    items = MenuItem.objects.filter(enabled=True, menu=menu) \
        .order_by('menu_digit')
    if len(items) == 0:
        raise Http404("Call Center menu {} has no items.".format(menu.name))

    return items


@twilio_view
def call_menu(request, name):
    response = VoiceResponse()
    menu = get_menu(name)
    items = get_menu_items(menu)

    # start twilio menu response
    with response.gather(
        num_digits=1, action=call_reverse(name, "call-action"), method="POST",
        timeout=10
    ) as g:
        last_digit = -1
        menu_text = ""
        if menu.greeting_text is not None:
            menu_text += menu.greeting_text
        for item in items:
            # skip empty items
            if not item.menu_text and not item.action_text \
                    and not item.action_phone:
                continue
            if last_digit >= item.menu_digit:
                continue

            last_digit = item.menu_digit

            if item.menu_text:
                menu_text += " Press {} {}.".format(item.menu_digit,
                                                    item.menu_text)

        twilio_say(menu, g, menu_text)
    return response


@twilio_view
def call_action(request, name):
    response = VoiceResponse()
    menu = get_menu(name)
    items = get_menu_items(menu)
    action_text = None
    action_phone = None
    action_url = None
    next_menu = name
    next_page = None

    query_dict = get_query_dict(request)
    digit = query_dict['Digits']

    digit_items = items.filter(menu_digit=digit)
    if len(digit_items):
        item = digit_items.first()

        if item.action_text:
            action_text = item.action_text
        if item.action_phone:
            action_phone = item.action_phone
            if action_text is None:
                action_text = twilio_default_transfer
        if item.action_url:
            action_url = item.action_url
        elif item.action_submenu:
            next_menu = item.action_submenu.name
            next_page = "call-menu"

    if action_text is not None:
        twilio_say(menu, response, action_text)
    if action_phone is None:
        next_page = "call-menu"
        if action_text is not None:
            response.pause(1)
    else:
        if next_page is None:
            next_page = "call-end"
        response.dial(action_phone)
    if action_url is None:
        action_url = call_reverse(next_menu, next_page)
    response.redirect(action_url)
    return response


@twilio_view
def call_end(request, name):
    response = VoiceResponse()
    menu = get_menu(name)
    twilio_say(menu, response, 'Goodbye.')
    response.hangup()
    return response
