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
3. Add `TWILIO_CALL_CENTER_VOICEMAIL_EMAIL` to settings.py
```python
TWILIO_CALL_CENTER_VOICEMAIL_EMAIL=os.environ.get(
        'TWILIO_CALL_CENTER_VOICEMAIL_EMAIL', 'voicemail@your-domain.com')
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

## How to use the call center
### Ensure Twilio credentials are set
Preferrably as environment variables, set `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`

### Prepare the menus
In the admin page there exists several types of objects:
1. Menus - a group of menu items
2. Menu items - one item in the menu
3. Voices - any voice that Twilio supports https://www.twilio.com/docs/voice/twiml/say#voice
4. Mailbox numbers - voicemail box or phone number with the option to send to voicemail
5. Voicemails - a recorded voicemail message with the transcription

### Set Twilio Webhook
Login to your twilio account and edit the settings for the necessary phone number.
You can obtain the link from the list of Menus under the `WEBHOOK` column.

The webhook will be in this form
`https://my.domain.com/call-center/<menu name>/call-menu`
