from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

class TwilioCallCenterConfig(AppConfig):
    name = 'twilio_call_center'
    verbose_name = 'Twilio Call Center'
