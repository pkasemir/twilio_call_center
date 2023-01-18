# Twilio Call Center
A django app which allows user to create dynamic call center for use with Twilio.

## How to install into django webserver
1. Add `twilio_call_center.apps.TwilioCallCenterConfig` to settings.py `INSTALLED_APPS`
2. Add a path to gain access to urls.py, for example:
```python
    urlpatterns = [
        # other paths go here
        path('call-center/', include('twilio_call_center.urls'),
            name='twilio_call_center'),
```
3. Add emails to settings.py
```python
TWILIO_CALL_CENTER_VOICEMAIL_EMAIL=os.environ.get(
        'TWILIO_CALL_CENTER_VOICEMAIL_EMAIL', 'voicemail@your-domain.com')
TWILIO_CALL_CENTER_SMS_EMAIL=os.environ.get(
        'TWILIO_CALL_CENTER_SMS_EMAIL', 'sms@your-domain.com')
```
4. (Optional) add link to the SMS sending page in one of your apps templates
```html
<a href="{% url 'twilio_call_center:send-sms' %}">Send SMS message</a>
```

## Other settings
### `TWILIO_CALL_CENTER_ACTION_FUNCTIONS`
This setting allows you to call arbitrary functions from your code from a menu
item. It is a list of tuples, the first being the module, and second being the
function. The function can take the request and the response objects. The
function can return a string for the menu item to say after the function
finishes.
```python
# app_name/twilio_actions.py
def unlock_front_door(**kwargs):
    # call some code to unlock the door
    return "The door is now unlocked."

# settings.py
TWILIO_CALL_CENTER_ACTION_FUNCTIONS = [
    ('app_name.twilio_actions', 'unlock_front_door'),
    ]
```

### `TWILIO_CALL_CENTER_DEBUG_SITE`
This setting allows you to override the status callback url. Normally the site
will have the HTTPS protocol, but this will allow you to set HTTP protocol for
debug purposes.
```python
# local_settings.py
TWILIO_CALL_CENTER_DEBUG_SITE="http://93.93.10.10:8000"
```

### `TWILIO_CALL_CENTER_DEFAULT_COUNTRY`
This setting lets you choose which country to attempt parsing phone numbers.
It defaults to 'US', but consult `pypi` package `phonenumbers` documentation
for the function `phonenumbers.parse()`

## How to use the call center
### Ensure Twilio credentials are set
Preferrably as environment variables, set `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`

### Prepare the voice menus
In the admin page there exists several types of objects:
1. Menus - a group of menu items
2. Menu items - one item in the menu
3. Voices - any voice that Twilio supports https://www.twilio.com/docs/voice/twiml/say#voice
4. Mailbox numbers - voicemail box or phone number with the option to send to voicemail

### Prepare to send and receive SMS messages
1. Twilio numbers - the phone numbers you will send SMS messages from or
forward incoming messages
2. Add `twilio_call_center` permissions to the users who can send SMS messages

### Other objects
1. Voicemails - a recorded voicemail message with the transcription
2. Sms Messages - details about SMS messages that were sent and received

### Set Twilio Webhooks
Login to your twilio account and edit the settings for the necessary phone number.
#### Voice webhook
You can obtain the link from the list of Menus under the `WEBHOOK` column.

The webhook will be in this form
`https://my.domain.com/call-center/<menu name>/call-menu`
#### Messageing webhook
The SMS webhook is at the root of the call center plus `/sms-incoming`

For example `https://my.domain.com/call-center/sms-incoming`
