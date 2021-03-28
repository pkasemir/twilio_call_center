# Twilio Call Center
A django app which allows user to create dynamic call center for use with Twilio.

## How to install into django webserver
1. Add `twilio_call_center.apps.TwilioCallCenterConfig` to settings.py `INSTALLED_APPS`
2. Add a path to gain access to urls.py, for example:

        urlpatterns = [
            # other paths go here
            path('call-center/', include('twilio_call_center.urls'),
                name='twilio_call_center'),

## How to use the call center
### Ensure Twilio credentials are set
Preferrably as environment variables, set `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`

### Prepare the menus
In the admin page there exists three types of objects:
1. Menus - a group of menu items
2. Menu items - one item in the menu
3. Voices - any voice that Twilio supports https://www.twilio.com/docs/voice/twiml/say#voice

### Set Twilio Webhook
Login to your twilio account and edit the settings for the necessary phone number.
You can obtain the link from the list of Menus under the `WEBHOOK` column.

The webhook will be in this form
`https://my.domain.com/call-center/<menu name>/call-menu`
