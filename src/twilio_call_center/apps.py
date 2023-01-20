from importlib import import_module

from django.apps import AppConfig, apps
from django.conf import settings


class TwilioCallCenterConfig(AppConfig):
    name = 'twilio_call_center'
    verbose_name = 'Twilio Call Center'

    def ready(self):
        try:
            action_functions = settings.TWILIO_CALL_CENTER_ACTION_FUNCTIONS
        except:
            action_functions = []
        self.action_functions = {m + '.' + f: getattr(import_module(m), f)
                                 for m, f in action_functions}

def my_app():
    return apps.get_app_config(TwilioCallCenterConfig.name)
