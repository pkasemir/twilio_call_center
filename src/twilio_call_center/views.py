import logging
import re

from apscheduler.jobstores.base import JobLookupError
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import Http404, HttpResponse, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.formats import localize
from django.utils.html import strip_tags, escape
from django.utils.safestring import SafeText
from django.views.generic.edit import FormView



from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse

from .apps import my_app
from .forms import SendSmsForm
from .models import Menu, MenuItem, Voicemail, twilio_default_transfer, \
    twilio_default_voice, SmsMessage, TwilioNumber
from .schedule import scheduler
from .utils import twilio_client, twilio_view, phone_numbers_equal


logger = logging.getLogger(__name__)


def twilio_callback_site(current_site):
    twilio_debug_site = getattr(settings, 'TWILIO_CALL_CENTER_DEBUG_SITE', None)
    if twilio_debug_site:
        return twilio_debug_site
    else:
        return "https://{}".format(current_site)


class FormViewWithErrorDisplay(FormView):
    extra_tags = ''

    def add_message(self, level, message, **kwargs):
        if "extra_tags" not in kwargs:
            kwargs["extra_tags"] = self.extra_tags
        messages.add_message(self.request, level, message, **kwargs)

    def info(self, message, **kwargs):
        self.add_message(messages.INFO, message, **kwargs)

    def warning(self, message, **kwargs):
        self.add_message(messages.WARNING, message, **kwargs)

    def error(self, message, **kwargs):
        self.add_message(messages.ERROR, message, **kwargs)


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


def call_reverse(name, page, **kwargs):
    reverse_args = {"name":name}
    reverse_args.update(kwargs)
    return reverse("twilio_call_center:" + page, kwargs=reverse_args)


def pin_reverse(name, digit):
    return call_reverse(name, 'call-pin', digit=digit)


def voicemail_reverse(name, digit):
    return call_reverse(name, 'voicemail', digit=digit)


def voicemail_sms_reverse(name, digit):
    return call_reverse(name, 'voicemail-sms-cb', digit=digit)


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
        if menu.greeting_text:
            menu_text += menu.greeting_text + '.'
        for item in items:
            # skip empty items
            if not item.menu_text and not item.action_text \
                    and not item.action_mailbox:
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
def call_action(request, name, digit=None):
    ''' Takes both action and pin urls
        <name>/call-action
        <name>/call-pin/<digit>
    '''
    response = VoiceResponse()
    menu = get_menu(name)
    items = get_menu_items(menu)
    pin = None
    action_text = None
    action_phone = None
    action_voicemail = None
    action_url = None
    action_function = None
    next_menu = name
    next_page = None

    query_dict = get_query_dict(request)
    if digit is None:
        digit = query_dict['Digits']
    else:
        pin = query_dict['Digits']

    digit_items = items.filter(menu_digit=digit)
    if len(digit_items):
        item = digit_items.first()

        pin_digits_list = item.get_pin_digits_list()
        if len(pin_digits_list):
            if pin is None:
                with response.gather(
                    finish_on_key='#', action=pin_reverse(name, digit),
                    method="POST", timeout=10
                ) as g:
                    pin_text = "Enter your pin followed by pound."
                    if item.pin_text:
                        pin_text = item.pin_text
                    twilio_say(menu, g, pin_text)
                return response
            else:
                if pin not in pin_digits_list:
                    twilio_say(menu, response, 'Invalid entry.')
                    response.pause(1)
                    response.redirect(call_reverse(name, 'call-menu'))
                    return response

        if item.action_text:
            action_text = item.action_text
        if item.action_mailbox:
            mailbox = item.action_mailbox
            if mailbox.should_send_voicemail():
                action_text = ''
                if mailbox.number_currently_unavailable():
                    action_text = "This connection is currently not available."
                action_text += " Please leave a message after the beep."
                action_voicemail=voicemail_reverse(name, digit)
            else:
                action_phone = mailbox.phone
                if action_phone and action_text is None:
                    action_text = twilio_default_transfer
        if item.action_url:
            action_url = item.action_url
        elif item.action_submenu:
            next_menu = item.action_submenu.name
            next_page = "call-menu"
        if item.action_function:
            action_function = item.action_function

    if action_function is not None:
        func = my_app().action_functions.get(action_function, None)
        if func is not None:
            func_str = func(request=request, response=response)
            if func_str is not None:
                action_text = func_str

    if action_text is not None:
        twilio_say(menu, response, action_text + '.')
    if action_phone is None:
        next_page = "call-menu"
        if action_text is not None:
            response.pause(1)
    else:
        if next_page is None:
            next_page = "call-end"

    if action_voicemail is not None:
        response.record(action=action_voicemail,
                        transcribeCallback=action_voicemail)
    else:
        if action_phone is not None:
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


def voicemail_notification_job(recording_sid, current_site):
    voicemail = Voicemail.objects.get(sid=recording_sid)
    send_voicemail_notifications(voicemail, current_site)


def send_voicemail_notifications(voicemail, current_site):
    mailbox = voicemail.mailbox
    if mailbox is None:
        return
    email_list = mailbox.get_email_list()
    phone_list = mailbox.get_phone_list()
    if len(email_list) == 0 and len(phone_list) == 0:
        return

    html = '''Hello,<br>
<br>
Call center option [{menu_item}] mailbox [{mailbox}] received voicemail from {from_phone}.<br>
<br>
Recording is at {url}'''.format(menu_item=voicemail.menu_item,
                                mailbox=mailbox,
                                from_phone=voicemail.from_phone,
                                url=voicemail.url)

    if voicemail.transcription_status:
        html += '''<br>
<br>
Transcription {}'''.format(voicemail.transcription_status)
        if voicemail.transcription_status == 'completed':
            html += ''':<br>
'''
            html += voicemail.transcription

    text_message = strip_tags(html)
    if len(email_list):
        send_mail('Received {} voicemail from {}'.format(voicemail.menu_item,
                                                         voicemail.from_phone),
                  text_message,
                  settings.TWILIO_CALL_CENTER_VOICEMAIL_EMAIL,
                  email_list,
                  html_message=html)

    if len(phone_list):
        callback_site = twilio_callback_site(current_site)
        name = digit = 'unknown'
        menu_item = voicemail.menu_item
        if menu_item:
            digit = menu_item.menu_digit
            menu = menu_item.menu
            if menu:
                name = menu.name
        for to_number in phone_list:
            kwargs = {
                'body': text_message,
                'to': to_number,
                'from_': mailbox.notification_phone.phone,
                'status_callback': callback_site + voicemail_sms_reverse(name,
                                                                         digit),
            }

            twilio_client.messages.create(**kwargs)


def handle_sms_cb_status(request, cb_type):
    query_dict = get_query_dict(request)
    no_status = 'no status'
    status = query_dict.get('MessageStatus', no_status)
    if status in ['failed', 'undelivered', no_status]:
        logger.error("{} failed with status: {}".format(cb_type, status))
    return HttpResponse(status=204)


@twilio_view
def voicemail_sms_cb(request, name, digit):
    cb_type = "Voicemail notification SMS for {} digit {}".format(
            name, digit)
    return handle_sms_cb_status(request, cb_type)


@twilio_view
def voicemail(request, name, digit):
    query_dict = get_query_dict(request)
    current_site = get_current_site(request)
    recording_sid = query_dict['RecordingSid']
    transcription = query_dict.get('TranscriptionText', None)
    transcription_status = query_dict.get('TranscriptionStatus', None)
    menu = get_menu(name)
    items = get_menu_items(menu).filter(menu_digit=digit)

    defaults=dict(call_sid=query_dict['CallSid'],
                  from_phone=query_dict['From'],
                  to_phone=query_dict['To'],
                  url=query_dict['RecordingUrl'],
                  status=query_dict['CallStatus'],
                  last_activity=timezone.now())
    if transcription is not None:
        defaults['transcription'] = transcription
    if transcription_status is not None:
        defaults['transcription_status'] = transcription_status
    if len(items) > 0:
        menu_item = items.first()
        defaults['menu_item'] = menu_item
        defaults['mailbox'] = menu_item.action_mailbox

    voicemail, _ = Voicemail.objects.update_or_create(
            sid=recording_sid,
            defaults=defaults)

    # We need settings.TWILIO_CALL_CENTER_VOICEMAIL_EMAIL, so make sure it
    # exists, else raise an exception which will email admins
    _ = settings.TWILIO_CALL_CENTER_VOICEMAIL_EMAIL
    job_id = "transcript-" + recording_sid
    if transcription_status is None:
        scheduler.add_job(voicemail_notification_job, 'date',
                          run_date=timezone.now() + timedelta(minutes=5),
                          args=[recording_sid, current_site], id=job_id)
    else:
        try:
            scheduler.remove_job(job_id)
        except JobLookupError:
            pass
        send_voicemail_notifications(voicemail, current_site)

    response = VoiceResponse()
    twilio_say(menu, response, 'Thanks for the voicemail. Goodbye.')
    response.hangup()
    return response


def sms_to_email(query_dict, twilio_phone, html):
    if html:
        def html_wrap(pre, value="", post=""):
            return pre + value + post
    else:
        def html_wrap(pre, value="", post=""):
            return value
    msg = ""
    msg += html_wrap('<html><body>')

    box_style = "; ".join([
        'border: thin solid black',
        'border-radius: 1em',
        'display: inline-block',
        'padding: 1em',
    ])
    img_style = "; ".join([
        'max-width: 100%',
        'max-height: 100%',
    ])
    msg += html_wrap('<p><span style="{}">'.format(box_style),
                     query_dict.get('Body', ''),
                     '</span></p>')
    try:
        num_media = int(query_dict.get('NumMedia', '0'))
        for i in range(num_media):
            media_url = query_dict.get('MediaUrl{}'.format(i), None)
            if media_url is None:
                continue
            media_type = query_dict.get(
                'MediaContentType{}'.format(i), "media")
            msg += html_wrap('<br />', '\n')
            if re.match("image/", media_type):
                msg += html_wrap('<img style="{}" alt="'.format(img_style),
                                 media_type,
                                 '" ')
                if not html:
                    msg += ' '
                msg += html_wrap('src="',
                                 media_url,
                                 '">')
            else:
                if not html:
                    msg += media_type + " "
                msg += html_wrap('<a href="',
                                 media_url,
                                 '">{}</a>'.format(media_type))
    except:
        logger.error("Could not prepare media for sms to email {}".format(
            query_dict.get('From', 'unknown')))

    msg += html_wrap('<p>',
                     '\nFrom: {} '.format(query_dict.get('From', 'unknown')))
    msg += html_wrap('<br />',
                     '\nTo: {} '.format(twilio_phone),
                     '</p>')
    msg += html_wrap('</body></html>')
    return msg


def sms_forward(current_site, twilio_phone, to_number, query_dict):
    callback_site = twilio_callback_site(current_site)

    msg = ''
    msg += '{}:{} received a message from {}:\n'.format(
        current_site, twilio_phone, query_dict.get('From', 'unknown'))
    msg += query_dict.get('Body', '')
    kwargs = {
        'body': msg,
        'to': to_number,
        'from_': twilio_phone.phone,
        'status_callback': callback_site + reverse('twilio_call_center:sms-forward-cb'),
    }
    try:
        num_media = int(query_dict.get('NumMedia', '0'))
        for i in range(num_media):
            media_url = query_dict.get('MediaUrl{}'.format(i), None)
            if media_url is None:
                continue
            if 'media_url' not in kwargs:
                kwargs['media_url'] = []
            kwargs['media_url'].append(media_url)
    except:
        logger.error("Could not prepare media for sms forward {}".format(
            query_dict.get('From', 'unknown')))

    twilio_client.messages.create(**kwargs)


@twilio_view
def sms_forward_cb(request):
    return handle_sms_cb_status(request, "Forward SMS")


@twilio_view
def sms_incoming(request):
    query_dict = get_query_dict(request)
    current_site = get_current_site(request)
    twilio_phone = None
    to_number = query_dict.get('To', None)
    if to_number is None:
        logger.error("Twilio API call has no 'To' field: " + str(query_dict))
        return MessagingResponse()

    update_sms_message("Incoming SMS", query_dict)

    for phone in TwilioNumber.objects.all():
        if phone_numbers_equal(phone.phone, to_number):
            twilio_phone = phone
            break

    if twilio_phone is None:
        logger.error(
            "Couldn't find matching TwilioNumber for incoming SMS. To: " +
            to_number)
        return MessagingResponse()

    email_to = twilio_phone.get_forward_email_list()
    if len(email_to):
        # We need settings.TWILIO_CALL_CENTER_SMS_EMAIL, so make sure it
        # exists, else raise an exception which will email admins
        _ = settings.TWILIO_CALL_CENTER_SMS_EMAIL
        try:
            send_mail('SMS to {} from {}'.
                            format(current_site,
                                   query_dict.get('From', 'unknown')),
                      sms_to_email(query_dict, twilio_phone, False),
                      settings.TWILIO_CALL_CENTER_SMS_EMAIL,
                      email_to,
                      html_message=sms_to_email(query_dict, twilio_phone, True),
                      )
        except Exception as e:
            logger.error('Unable to send SMS email to {}'.format(email_to))
            logger.error(str(e))
    sms_to = twilio_phone.get_forward_phone_list()
    for to_number in sms_to:
        try:
            sms_forward(current_site, twilio_phone, to_number, query_dict)
        except Exception as e:
            logger.error('Unable to forward SMS to {}'.format(to_number))
            logger.error(str(e))
    return MessagingResponse()


def update_sms_message(type_str, query_dict):
    sid = query_dict.get('MessageSid', None)
    if not sid:
        logger.warning("{} doesn't have MessageSid".format(type_str))
        return None
    else:
        msg_kwargs = dict(from_phone=query_dict.get('From', 'unknown'),
                          to_phone=query_dict.get('To', 'unknown'),
                          message=query_dict.get('Body', 'unknown'),
                          status=query_dict.get('SmsStatus', 'unknown'),
                          last_activity=timezone.now())
        msg, _ = SmsMessage.objects.update_or_create(sid=sid,
                                                     defaults=msg_kwargs)
        return msg


def send_sms(current_site, from_number, to_number, msg):
    callback_site = twilio_callback_site(current_site)
    result = {'id': None, 'sid': None, 'error': None}

    kwargs = {
        'body': msg,
        'to': to_number,
        'from_': from_number,
        'status_callback': callback_site + reverse('twilio_call_center:send-sms-cb'),
    }

    try:
        msg = twilio_client.messages.create(**kwargs)
    except Exception as e:
        # remove CLI color chars
        s = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', str(e))
        s = re.sub(r'\n', '<br>', escape(s))
        result['error'] = SafeText(s)
        return result

    if not msg.sid:
        result['error'] = "No SMS sid returned: {}".format(msg._properties)
        return result

    result['sid'] = msg.sid
    result['status'] = getattr(msg, 'status', 'unknown')
    result['error'] = getattr(msg, 'error_message', None)

    sms_message = update_sms_message("SMS send", dict(
        MessageSid=msg.sid,
        From=getattr(msg, 'from_', 'unknown'),
        To=getattr(msg, 'to', 'unknown'),
        Body=getattr(msg, 'body', 'unknown'),
        SmsStatus=result['status'],
    ))

    if sms_message:
        result['id'] = sms_message.id

    return result


@twilio_view
def send_sms_cb(request):
    query_dict = get_query_dict(request)
    update_sms_message("SMS send callback", query_dict)
    return handle_sms_cb_status(request, 'Sending SMS')


def sms_status(request):
    if not request.user.has_perm('twilio_call_center.view_smsmessage'):
        return JsonResponse({'error':
            'You do not have permissions to view SMS messages'})

    query_dict = get_query_dict(request)
    sid = query_dict.get('sid', None)
    if not sid:
        return JsonResponse({'error': 'SMS status requires the SID'})

    msg = SmsMessage.objects.filter(sid=sid).first()
    if not msg:
        return JsonResponse({'error': 'SMS does not exist for SID',
                             'sid': sid})

    response = dict(error=None)
    for field in msg._meta.get_fields():
        response[field.name] = getattr(msg, field.name)
        if field.name == 'last_activity':
            response[field.name] = localize(
                timezone.localtime(response[field.name]))

    return JsonResponse(response)


class SendSmsView(FormViewWithErrorDisplay):
    template_name = 'twilio_call_center/send_sms.html'
    form_class = SendSmsForm
    success_url = reverse_lazy('twilio_call_center:send-sms')
    last_msg = 'last_msg'

    def form_valid(self, form):
        current_site = get_current_site(self.request)
        msg = form.cleaned_data['message']
        to_number = form.cleaned_data['to_phone']
        from_number = form.cleaned_data['from_phone']
        result = send_sms(current_site, from_number.phone, to_number, msg)
        if result['sid']:
            self.info(result['sid'], extra_tags=self.last_msg)
            sms_link = "SMS message"
            if result['id']:
                link = reverse("admin:twilio_call_center_smsmessage_change",
                               args=(result['id'],))
                sms_link = '<a href="{}">{}</a>'.format(link, sms_link)
            self.info(SafeText(
                '{} created with status: {}'.
                format(sms_link, result['status'])))
        if result['error']:
            self.error(result['error'])
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        message_list = messages.get_messages(self.request)
        context['messages'] = []
        for message in message_list:
            if message.extra_tags == self.last_msg:
                context[self.last_msg] = message.message
            else:
                context['messages'].append(message)
                if message.level == messages.ERROR:
                    context['has_error'] = True

        return context
